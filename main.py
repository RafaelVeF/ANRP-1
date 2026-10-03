import pygame
import sys
import textwrap
import re
import threading
import random
import pyperclip
import pyttsx3
import os
import queue
import time
from PIL import Image
from brain import get_bot_response_stream, user_memory, bot_learning, system_info_queue
import voice_worker

# --- 1. FONCTIONS DE CHARGEMENT ---
FACES_DIR = "faces"
if not os.path.exists(FACES_DIR):
    os.makedirs(FACES_DIR)

def load_face_grid(mood):
    filepath = os.path.join(FACES_DIR, f"{mood}.txt")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return [line.strip() for line in f.readlines()]
    return load_face_grid("NEUTRE")

def load_gif(filename):
    """Découpe un GIF en une liste de surfaces Pygame."""
    if not os.path.exists(filename):
        return None
    pil_img = Image.open(filename)
    frames = []
    try:
        while True:
            frame = pil_img.copy().convert("RGBA")
            mode = frame.mode
            size = frame.size
            data = frame.tobytes()
            pygame_surface = pygame.image.frombytes(data, size, mode)
            frames.append(pygame_surface)
            pil_img.seek(pil_img.tell() + 1)
    except EOFError:
        pass
    return frames

pygame.init()

# --- INITIALISATION TTS ---
engine = pyttsx3.init()
engine.setProperty('rate', 140)
voices = engine.getProperty('voices')
for voice in voices:
    if 'paul' in voice.name.lower() or 'male' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

tts_queue = queue.Queue()

is_speaking = False
def tts_worker():
    global is_speaking
    while True:
        text = tts_queue.get()
        if text is None: break
        if text.strip():
            is_speaking = True
            engine.say(text)
            engine.runAndWait()
            is_speaking = False

tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

# --- ÉCRAN ---
infoObject = pygame.display.Info()
WIDTH, HEIGHT = int(infoObject.current_w * 0.6), int(infoObject.current_h * 0.6)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("ANTIGRAVITY UNIT-95")

MONKEY_GIF = load_gif("monkey-annoying.gif")
monkey_frame_idx = 0
monkey_timer = 0

# --- COULEURS & POLICES ---
BLUE_BG   = (10, 20, 15)
TERM_BG   = (5, 5, 10)
TERM_TEXT = (50, 255, 50)
COLOR_GREEN = (50, 255, 100)
COLOR_RED   = (255, 50, 50)
BLOCK_SIZE  = 25
font      = pygame.font.SysFont("consolas", 18)
tree_font = pygame.font.SysFont("consolas", 14)

TERM_HEIGHT = HEIGHT // 5
TERM_Y = HEIGHT - TERM_HEIGHT
term_w = int(WIDTH * 0.7)
info_w = WIDTH - term_w
term_rect = pygame.Rect(0, TERM_Y, term_w, TERM_HEIGHT)
info_rect = pygame.Rect(term_w, TERM_Y, info_w, TERM_HEIGHT)
char_width = font.size("A")[0]
max_chars_per_line = max(10, (term_w - 40) // char_width)
info_chars_per_line = max(10, (info_w - 40) // char_width)
line_height = font.get_height() + 5
max_display_lines = (TERM_HEIGHT - 40) // line_height

chat_scroll_y = 0
system_info_log = ["--- SYSTEM INFO ---"]
system_info_scroll_y = 0

# --- ÉTAT ÉMOTIONNEL ---
current_mood = "NEUTRE"
display_mood = "NEUTRE"
anim_timer = 0
is_animating = False

# --- STATS VITALES (0.0 à 1.0) ---
vital_energy    = 1.0   # Nourriture
vital_happiness = 1.0   # Bonheur (caresser / jouer)
vital_health    = 1.0   # Santé / Intégrité

# --- BOUTONS VITAUX ---
# Calculés dynamiquement dans draw_vitals(), stockés ici pour détection clic
btn_feed   = pygame.Rect(0, 0, 1, 1)
btn_pet    = pygame.Rect(0, 0, 1, 1)
btn_repair = pygame.Rect(0, 0, 1, 1)

# --- CHAT & STREAM ---
user_input = ""
cursor_pos = 0
history = []
chat_log = ["--- UNIT-95 ONLINE ---", "MONKEY MODULE LOADED."]

is_thinking = False
is_typing = False
bot_response_data = None
target_text = ""
typed_text = ""
tts_sentence_buffer = ""
response_queue = queue.Queue()
user_input_history_save = ""

# --- TEMPS ET SUIVI PERFORMANCE (ETA & SPEED) ---
gen_start_time = 0.0
stream_start_time = 0.0
generated_tokens_count = 0
last_token_speed = 0.0
avg_response_duration = 5.0

# --- MÉMOIRE ARBRE ---
tree_scroll_y = 0
tree_zoom = 1.0
tree_collapsed = False
tree_toggle_rect = pygame.Rect(390, 90, 20, 20)

# --- SCANLINES ---
scanline_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for y in range(0, HEIGHT, 4):
    pygame.draw.line(scanline_surf, (0, 0, 0, 80), (0, y), (WIDTH, y))

# ─────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────
def wrap_text(text, max_width):
    return textwrap.wrap(text, width=max_width)

def fetch_response_thread(prompt, hist):
    vital_str = get_vital_status_str()
    for item_type, content in get_bot_response_stream(prompt, hist, vital_status=vital_str):
        response_queue.put((item_type, content))

def trigger_care_response(care_type):
    """Déclenche une réponse spontanée de l'agent après un soin."""
    global user_input_history_save, is_thinking, gen_start_time, generated_tokens_count
    if is_thinking or is_typing:
        return
    messages = {
        "feed":   "[SYSTEM] L'utilisateur vient de te recharger en énergie. Tu es repu. Réagis brièvement (1-2 phrases max).",
        "pet":    "[SYSTEM] L'utilisateur vient de te caresser. Tu te sens aimé. Réagis brièvement (1-2 phrases max).",
        "repair": "[SYSTEM] L'utilisateur vient de réparer ton intégrité. Tu te sens neuf. Réagis brièvement (1-2 phrases max)."
    }
    msg = messages.get(care_type, "")
    if msg:
        user_input_history_save = msg
        is_thinking = True
        gen_start_time = time.time()
        generated_tokens_count = 0
        threading.Thread(target=fetch_response_thread, args=(msg, history.copy()), daemon=True).start()

def get_vital_status_str():
    """Retourne un résumé des vitales pour injection dans le prompt LLM."""
    return (
        f"ENERGY={int(vital_energy*100)}% | "
        f"HAPPINESS={int(vital_happiness*100)}% | "
        f"INTEGRITY={int(vital_health*100)}%"
    )

def decay_vitals():
    """Décrémente les stats vitales aléatoirement (5-20%) à chaque requête."""
    global vital_energy, vital_happiness, vital_health
    vital_energy    = max(0.0, vital_energy    - random.uniform(0.05, 0.20))
    vital_happiness = max(0.0, vital_happiness - random.uniform(0.05, 0.20))
    vital_health    = max(0.0, vital_health    - random.uniform(0.02, 0.10))

def get_vital_mood_override():
    """Calcule l'humeur forcée si une stat est critique (< 30%)."""
    if vital_health < 0.30:
        return "PEUR"
    if vital_energy < 0.30:
        return "TRISTE"
    if vital_happiness < 0.30:
        return "COLERE"
    return None

def count_keys(d):
    count = 0
    for k, v in d.items():
        if isinstance(v, dict):
            count += count_keys(v)
        else:
            count += 1
    return count

def get_tree_lines(d, prefix=""):
    lines = []
    if isinstance(d, dict):
        keys = list(d.keys())
        for i, k in enumerate(keys):
            is_last = (i == len(keys) - 1)
            connector = "└── " if is_last else "├── "
            lines.append((prefix + connector + str(k), (50, 200, 255)))
            extension = "    " if is_last else "│   "
            lines.extend(get_tree_lines(d[k], prefix + extension))
    else:
        lines.append((prefix + "└── " + str(d), (255, 150, 50)))
    return lines

# ─────────────────────────────────────────────────────────
#  DRAW : PIXEL FACE
# ─────────────────────────────────────────────────────────
def draw_pixel_face(surface, grid, center_x, center_y, color):
    if not grid: return
    grid_height = len(grid) * BLOCK_SIZE
    grid_width  = len(grid[0]) * BLOCK_SIZE
    start_x = center_x - (grid_width  // 2)
    start_y = center_y - (grid_height // 2)
    for row_idx, row in enumerate(grid):
        for col_idx, char in enumerate(row):
            if char == 'X':
                px = start_x + (col_idx * BLOCK_SIZE)
                py = start_y + (row_idx * BLOCK_SIZE)
                core_rect = pygame.Rect(px, py, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
                pygame.draw.rect(surface, color, core_rect)

# ─────────────────────────────────────────────────────────
#  DRAW : MEMORY TREE (Gauche)
# ─────────────────────────────────────────────────────────
def draw_memory_tree(surface):
    TREE_X, TREE_W = 10, 350
    view_rect = pygame.Rect(TREE_X, 100, TREE_W, TERM_Y - 120)

    # Cadre fond
    if tree_collapsed:
        header_rect = pygame.Rect(TREE_X, 90, TREE_W, 30)
        pygame.draw.rect(surface, (8, 12, 18), header_rect)
        pygame.draw.rect(surface, (40, 80, 40), header_rect, 1)
    else:
        pygame.draw.rect(surface, (8, 12, 18), view_rect)
        pygame.draw.rect(surface, (40, 80, 40), view_rect, 1)

    title_surf = tree_font.render(" SYSTEM.MEMORY_TREE ", True, (40, 80, 40), (8, 12, 18))
    surface.blit(title_surf, (TREE_X + 10, 93))

    # Bouton repli
    toggle_x = TREE_X + TREE_W - 24
    tree_toggle_rect.x = toggle_x
    tree_toggle_rect.y = 90
    tree_toggle_rect.w = 20
    tree_toggle_rect.h = 20
    arrow_char = "▼" if not tree_collapsed else "▶"
    arrow_surf = tree_font.render(arrow_char, True, (200, 200, 200), (8, 12, 18))
    surface.blit(arrow_surf, (toggle_x + 3, 92))
    pygame.draw.rect(surface, (80, 80, 80), tree_toggle_rect, 1)

    if tree_collapsed:
        return

    lines = [("ROOT [MEMORY]", (255, 255, 255))] + get_tree_lines(user_memory)
    base_line_height = 17
    surf_height = max(100, len(lines) * base_line_height + 20)
    temp_surf = pygame.Surface((TREE_W, surf_height), pygame.SRCALPHA)

    y = 5
    for text, color in lines:
        txt_surf = tree_font.render(text, True, color)
        temp_surf.blit(txt_surf, (5, y))
        y += base_line_height

    if tree_zoom != 1.0:
        new_w = int(TREE_W * tree_zoom)
        new_h = int(surf_height * tree_zoom)
        temp_surf = pygame.transform.smoothscale(temp_surf, (new_w, new_h))

    old_clip = surface.get_clip()
    surface.set_clip(view_rect)
    surface.blit(temp_surf, (TREE_X + 5, 105 + tree_scroll_y))
    surface.set_clip(old_clip)

# ─────────────────────────────────────────────────────────
#  DRAW : VITAL SIGNS PANEL (Droite)
# ─────────────────────────────────────────────────────────
def draw_vitals(surface):
    global btn_feed, btn_pet, btn_repair

    PANEL_W = 300
    PANEL_X = WIDTH - PANEL_W - 10
    PANEL_Y = 100
    PANEL_H = TERM_Y - 120

    panel_rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    pygame.draw.rect(surface, (8, 10, 18), panel_rect)
    pygame.draw.rect(surface, (80, 40, 100), panel_rect, 1)

    title_surf = tree_font.render(" UNIT-95.VITAL_SIGNS ", True, (180, 80, 255), (8, 10, 18))
    surface.blit(title_surf, (PANEL_X + 10, PANEL_Y - 8))

    # --- Fonction locale pour dessiner une jauge ---
    def draw_bar(label, value, y_pos, fill_color, low_color, btn_label, btn_ref_key):
        bar_x = PANEL_X + 10
        bar_y = y_pos
        bar_w = PANEL_W - 20
        bar_h = 18

        # Label + valeur numérique
        pct = int(value * 100)
        color_label = (200, 200, 200) if value > 0.3 else (255, 80, 80)
        lbl_surf = tree_font.render(f"{label} : {pct}%", True, color_label)
        surface.blit(lbl_surf, (bar_x, bar_y))

        # Fond de jauge
        bar_bg_rect = pygame.Rect(bar_x, bar_y + 18, bar_w, bar_h)
        pygame.draw.rect(surface, (20, 20, 30), bar_bg_rect)

        # Remplissage de jauge avec couleur critique
        active_color = low_color if value < 0.3 else fill_color
        fill_w = max(0, int(bar_w * value))
        pygame.draw.rect(surface, active_color, pygame.Rect(bar_x, bar_y + 18, fill_w, bar_h))
        pygame.draw.rect(surface, (50, 50, 60), bar_bg_rect, 1)

        # Bouton d'action
        btn_rect = pygame.Rect(bar_x, bar_y + 44, bar_w, 22)
        btn_color = (20, 40, 20) if value > 0.5 else (40, 15, 15)
        pygame.draw.rect(surface, btn_color, btn_rect)
        pygame.draw.rect(surface, (100, 100, 100), btn_rect, 1)
        btn_surf = tree_font.render(f"[ {btn_label} ]", True, (180, 255, 180))
        btn_text_x = btn_rect.x + (btn_rect.w - btn_surf.get_width()) // 2
        surface.blit(btn_surf, (btn_text_x, btn_rect.y + 3))

        return btn_rect

    spacing = PANEL_H // 3
    y0 = PANEL_Y + 20

    btn_feed   = draw_bar("ENERGY   [FEED]",    vital_energy,    y0,               (50, 200, 100), (255, 60, 60),  "RECHARGE ENERGIE",  "feed")
    btn_pet    = draw_bar("HAPPINESS [PET]",     vital_happiness, y0 + spacing,     (80, 130, 255), (255, 140, 20), "CARESSER / JOUER", "pet")
    btn_repair = draw_bar("INTEGRITY [REPAIR]",  vital_health,    y0 + spacing * 2, (200, 200, 50), (255, 30, 100), "REPARER SYSTEME", "repair")

    # Icône critique globale
    if vital_energy < 0.3 or vital_happiness < 0.3 or vital_health < 0.3:
        warn_surf = tree_font.render("⚠ ÉTAT CRITIQUE DÉTECTÉ", True, (255, 60, 60))
        surface.blit(warn_surf, (PANEL_X + 10, PANEL_Y + PANEL_H - 25))

# ─────────────────────────────────────────────────────────
#  DRAW : DASHBOARD (Haut)
# ─────────────────────────────────────────────────────────
def draw_dashboard(surface, fnt):
    dash_rect = pygame.Rect(0, 0, WIDTH, 80)
    pygame.draw.rect(surface, (15, 20, 25), dash_rect)
    pygame.draw.line(surface, (50, 100, 50), (0, 80), (WIDTH, 80), 2)

    mem_count   = count_keys(user_memory)
    learn_count = count_keys(bot_learning)

    now = time.time()
    if is_thinking:
        elapsed = now - gen_start_time
        est_total = max(1.0, avg_response_duration)
        state_str = f"THINKING... ({elapsed:.1f}s / ~{est_total:.1f}s)"
        state_color = COLOR_RED
    elif is_typing:
        elapsed = now - stream_start_time
        total_elapsed = now - gen_start_time
        state_str = f"STREAMING ({last_token_speed:.1f} t/s | {total_elapsed:.1f}s)"
        state_color = COLOR_GREEN
    else:
        state_str = "IDLE"
        state_color = (100, 100, 100)

    txt_state = fnt.render(f"SYS_STATE : {state_str}", True, state_color)
    txt_mood  = fnt.render(f"CORE_MOOD : {current_mood}", True, COLOR_GREEN)
    txt_mem   = fnt.render(f"MEMORY_NODES : {mem_count}", True, (50, 200, 255))
    txt_learn = fnt.render(f"LEARN_NODES  : {learn_count}", True, (255, 150, 50))

    load_width = 220
    load_x = WIDTH // 2 - 110
    pygame.draw.rect(surface, (30, 30, 30), (load_x, 25, load_width, 15))

    if is_thinking:
        elapsed = now - gen_start_time
        est_total = max(1.0, avg_response_duration)
        pct = min(0.92, elapsed / est_total)
        active_w = int(load_width * pct)
        pygame.draw.rect(surface, COLOR_RED, (load_x, 25, active_w, 15))
        rem = max(0.0, est_total - elapsed)
        txt_load = fnt.render(f"NEURAL_LINK : ~{rem:.1f}s restants", True, COLOR_RED)
    elif is_typing:
        total_elapsed = now - gen_start_time
        pct = min(0.99, total_elapsed / max(1.0, avg_response_duration))
        active_w = int(load_width * pct)
        pygame.draw.rect(surface, COLOR_GREEN, (load_x, 25, active_w, 15))
        txt_load = fnt.render(f"NEURAL_LINK : {last_token_speed:.1f} tok/s", True, COLOR_GREEN)
    else:
        speed_str = f"{last_token_speed:.1f} t/s" if last_token_speed > 0 else "READY"
        txt_load = fnt.render(f"NEURAL_LINK : STABLE ({speed_str})", True, (100, 100, 100))

    pygame.draw.rect(surface, (60, 60, 60), (load_x, 25, load_width, 15), 1)
    surface.blit(txt_load,  (load_x, 45))
    surface.blit(txt_state, (20, 15))
    surface.blit(txt_mood,  (20, 45))
    surface.blit(txt_mem,   (WIDTH - 250, 15))
    surface.blit(txt_learn, (WIDTH - 250, 45))

# ─────────────────────────────────────────────────────────
#  BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────
clock   = pygame.time.Clock()
running = True

while running:

    # --- 1. ANIMATIONS DU VISAGE ---
    # Surcharge vitale : si état critique, forcer l'humeur de détresse
    vital_mood_override = get_vital_mood_override()

    if is_thinking:
        anim_timer -= 1
        if anim_timer <= 0:
            rand_val = random.random()
            if rand_val < 0.35:
                display_mood = "LOOK_L"; anim_timer = 18
            elif rand_val < 0.70:
                display_mood = "LOOK_R"; anim_timer = 18
            elif rand_val < 0.85:
                display_mood = "BLINK";  anim_timer = 8
            else:
                display_mood = "NEUTRE"; anim_timer = 25
    elif not is_typing:
        if vital_mood_override:
            display_mood = vital_mood_override
        elif not is_animating:
            if random.random() < 0.01:
                is_animating = True
                anim_timer = 10
                rand_val = random.random()
                if rand_val < 0.6:   display_mood = "BLINK"
                elif rand_val < 0.8: display_mood = "LOOK_L"
                else:                display_mood = "LOOK_R"
        else:
            anim_timer -= 1
            if anim_timer <= 0:
                is_animating = False
                display_mood = vital_mood_override if vital_mood_override else current_mood
    else:
        display_mood = current_mood

    # --- 2. RÉCUPÉRATION RÉPONSE EN FLUX (STREAM) ---
    while not response_queue.empty():
        item_type, content = response_queue.get_nowait()

        if item_type == "START":
            target_text = ""
            typed_text = ""
            tts_sentence_buffer = ""
            is_thinking = False
            is_typing = True
            stream_start_time = time.time()
            generated_tokens_count = 0

        elif item_type == "MOOD":
            match = re.match(r'\[(.*?)\]', content)
            if match:
                current_mood = match.group(1).strip().upper()
                display_mood = current_mood

        elif item_type == "TEXT":
            target_text += content
            typed_text  += content
            tts_sentence_buffer += content
            generated_tokens_count += 1
            st_elapsed = max(0.1, time.time() - stream_start_time)
            last_token_speed = generated_tokens_count / st_elapsed

            if content in ['.', '!', '?'] or '\n' in content:
                if tts_sentence_buffer.strip():
                    tts_queue.put(tts_sentence_buffer)
                    tts_sentence_buffer = ""

        elif item_type == "DONE":
            if tts_sentence_buffer.strip():
                tts_queue.put(tts_sentence_buffer)
                tts_sentence_buffer = ""

            history.append({"role": "user",      "content": user_input_history_save})
            history.append({"role": "assistant",  "content": f"[{current_mood}] {target_text}"})
            if len(history) > 6: history = history[-6:]

            is_typing = False
            tot_dur = max(0.5, time.time() - gen_start_time)
            avg_response_duration = 0.6 * avg_response_duration + 0.4 * tot_dur

            for ligne in wrap_text(f"UNIT-95: {target_text}", max_chars_per_line):
                chat_log.append(ligne)

            target_text = ""
            typed_text  = ""
            
    while not system_info_queue.empty():
        info_text = system_info_queue.get_nowait()
        system_info_log.append("="*20)
        for line in info_text.split('\n'):
            for wrapped in wrap_text(line, info_chars_per_line):
                system_info_log.append(wrapped)

    # --- 3. ÉVÉNEMENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Clics boutons ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Arbre mémoire : repli/dépli
            if tree_toggle_rect.collidepoint(event.pos):
                tree_collapsed = not tree_collapsed

            # Boutons vitaux
            elif btn_feed.collidepoint(event.pos) and not is_thinking and not is_typing:
                vital_energy = 1.0
                chat_log.append("> [SOIN] Énergie rechargée à 100%.")
                trigger_care_response("feed")

            elif btn_pet.collidepoint(event.pos) and not is_thinking and not is_typing:
                vital_happiness = 1.0
                chat_log.append("> [SOIN] Bonheur restauré à 100%.")
                trigger_care_response("pet")

            elif btn_repair.collidepoint(event.pos) and not is_thinking and not is_typing:
                vital_health = 1.0
                chat_log.append("> [SOIN] Intégrité réparée à 100%.")
                trigger_care_response("repair")

        # --- Redimensionnement ---
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.size
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            TERM_HEIGHT       = max(100, HEIGHT // 5)
            TERM_Y            = HEIGHT - TERM_HEIGHT
            term_w = int(WIDTH * 0.7)
            info_w = WIDTH - term_w
            term_rect = pygame.Rect(0, TERM_Y, term_w, TERM_HEIGHT)
            info_rect = pygame.Rect(term_w, TERM_Y, info_w, TERM_HEIGHT)
            max_chars_per_line = max(10, (term_w - 40) // char_width)
            info_chars_per_line = max(10, (info_w - 40) // char_width)
            max_display_lines  = max(1, (TERM_HEIGHT - 40) // line_height)
            scanline_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for y_sl in range(0, HEIGHT, 4):
                pygame.draw.line(scanline_surf, (0, 0, 0, 80), (0, y_sl), (WIDTH, y_sl))

        # --- Scroll & Zoom (arbre) ---
        if event.type == pygame.MOUSEWHEEL:
            mods = pygame.key.get_mods()
            m_pos = pygame.mouse.get_pos()
            if mods & pygame.KMOD_CTRL:
                tree_zoom = max(0.5, min(3.0, tree_zoom + event.y * 0.1))
            elif term_rect.collidepoint(m_pos):
                chat_scroll_y = max(0, chat_scroll_y + event.y)
            elif info_rect.collidepoint(m_pos):
                system_info_scroll_y = max(0, system_info_scroll_y + event.y)
            else:
                tree_scroll_y = min(0, tree_scroll_y + event.y * 20)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LALT:
                voice_worker.stop_recording_and_transcribe()
        
        # --- Clavier ---
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LALT:
                voice_worker.start_recording()
                
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL:
                if event.key == pygame.K_v:
                    user_input = user_input[:cursor_pos] + pyperclip.paste() + user_input[cursor_pos:]
                    cursor_pos = len(user_input)
                elif event.key == pygame.K_c:
                    pyperclip.copy(user_input)
                continue

            if event.key == pygame.K_ESCAPE:
                running = False
            elif not is_thinking and not is_typing:
                if event.key == pygame.K_RETURN:
                    chat_scroll_y = 0
                    if user_input.strip():
                        for l in wrap_text(f"> USER: {user_input}", max_chars_per_line):
                            chat_log.append(l)
                        is_thinking = True
                        gen_start_time = time.time()
                        generated_tokens_count = 0
                        user_input_history_save = user_input
                        decay_vitals()   # Décrémenter vitales à chaque requête
                        threading.Thread(
                            target=fetch_response_thread,
                            args=(user_input, history.copy()),
                            daemon=True
                        ).start()
                        user_input = ""
                        cursor_pos = 0
                elif event.key == pygame.K_LEFT:
                    cursor_pos = max(0, cursor_pos - 1)
                elif event.key == pygame.K_RIGHT:
                    cursor_pos = min(len(user_input), cursor_pos + 1)
                elif event.key == pygame.K_BACKSPACE:
                    if cursor_pos > 0:
                        user_input = user_input[:cursor_pos-1] + user_input[cursor_pos:]
                        cursor_pos -= 1
                elif event.unicode.isprintable():
                    user_input = user_input[:cursor_pos] + event.unicode + user_input[cursor_pos:]
                    cursor_pos += 1

    # Polling STT Queue
    try:
        stt_text = voice_worker.STT_QUEUE.get_nowait()
        if stt_text and not is_thinking and not is_typing:
            user_input = stt_text
            chat_scroll_y = 0
            for l in wrap_text(f"> USER (Voix): {user_input}", max_chars_per_line):
                chat_log.append(l)
            is_thinking = True
            gen_start_time = time.time()
            generated_tokens_count = 0
            user_input_history_save = user_input
            decay_vitals()
            threading.Thread(
                target=fetch_response_thread,
                args=(user_input, history.copy()),
                daemon=True
            ).start()
            user_input = ""
            cursor_pos = 0
    except queue.Empty:
        pass

    # --- 4. DESSIN ---
    screen.fill(BLUE_BG)

    # Visage : centré dans l'espace central (entre l'arbre et le panneau vitaux)
    face_grid = load_face_grid(display_mood)
    
    # Audio Visualizer logic
    if is_speaking:
        pulse = int(180 + 75 * abs(((pygame.time.get_ticks() // 10) % 50 - 25) / 25))
        face_color = (100, pulse, 255) # Couleur cyan/bleu vif quand il parle
        # Animation légère du visage (bouche)
        if len(face_grid) > 4:
            middle_idx = len(face_grid) // 2
            face_grid[middle_idx] = face_grid[middle_idx].replace("_", "O").replace("-", "o")
    elif voice_worker.IS_RECORDING:
        face_color = (255, 100, 100) # Rouge quand il écoute
    elif is_thinking:
        pulse = int(180 + 75 * abs(((pygame.time.get_ticks() // 20) % 50 - 25) / 25))
        face_color = (30, pulse, 80)
    else:
        face_color = COLOR_RED if current_mood in ["COLERE", "ERROR", "PEUR", "DEGOUT"] else COLOR_GREEN
        if vital_mood_override:
            face_color = (255, 80, 30) if vital_mood_override == "COLERE" else (80, 80, 200)

    face_center_x = WIDTH // 2
    face_center_y = (TERM_Y + 80) // 2
    draw_pixel_face(screen, face_grid, face_center_x, face_center_y, face_color)

    # Panneaux latéraux
    draw_memory_tree(screen)
    draw_vitals(screen)

    # Dashboard
    draw_dashboard(screen, font)

    # Terminal & System Info Panels
    pygame.draw.rect(screen, TERM_BG, term_rect)
    pygame.draw.rect(screen, (10, 15, 20), info_rect)
    pygame.draw.line(screen, (50, 100, 50), (0, TERM_Y), (WIDTH, TERM_Y), 3)
    pygame.draw.line(screen, (50, 100, 50), (term_w, TERM_Y), (term_w, HEIGHT), 2) # Ligne de séparation

    lignes_a_dessiner = list(chat_log)
    if is_typing:
        for l in wrap_text(f"UNIT-95: {typed_text}", max_chars_per_line):
            lignes_a_dessiner.append(l)

    # Définir le max scroll du chat
    max_scroll = max(0, len(lignes_a_dessiner) - max_display_lines + (1 if not is_thinking and not is_typing else 0))
    chat_scroll_y = min(chat_scroll_y, max_scroll)
    
    start_idx = max(0, len(lignes_a_dessiner) - max_display_lines - chat_scroll_y)
    end_idx = len(lignes_a_dessiner) - chat_scroll_y
    if end_idx <= start_idx: end_idx = len(lignes_a_dessiner)
    
    y_off = TERM_Y + 10
    for l in lignes_a_dessiner[start_idx:end_idx]:
        screen.blit(font.render(l, True, TERM_TEXT), (20, y_off))
        y_off += line_height

    if not is_thinking and not is_typing and chat_scroll_y == 0:
        txt_input = user_input[:cursor_pos] + "_" + user_input[cursor_pos:]
        screen.blit(font.render(f"~$ {txt_input}", True, TERM_TEXT), (20, y_off))
        
    # Dessin du Panel System Info
    sys_max_scroll = max(0, len(system_info_log) - max_display_lines)
    system_info_scroll_y = min(system_info_scroll_y, sys_max_scroll)
    
    s_start_idx = max(0, len(system_info_log) - max_display_lines - system_info_scroll_y)
    s_end_idx = len(system_info_log) - system_info_scroll_y
    if s_end_idx <= s_start_idx: s_end_idx = len(system_info_log)
    
    y_off_info = TERM_Y + 10
    for l in system_info_log[s_start_idx:s_end_idx]:
        screen.blit(font.render(l, True, (150, 200, 255)), (term_w + 10, y_off_info))
        y_off_info += line_height

    screen.blit(scanline_surf, (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()