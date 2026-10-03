import os
import json
import re
import subprocess
import time
import urllib.request
import urllib.error
import queue
import threading
from openai import OpenAI
import external_api
from system_actions import execute_action

# --- 0. AUTO-DÉMARRAGE DU SERVICE OLLAMA ---
def ensure_ollama_service():
    """Vérifie si Ollama tourne, sinon tente de démarrer le service en arrière-plan."""
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.5)
        if req.status == 200:
            return True
    except Exception:
        pass

    # Si le service ne répond pas, on essaie de le lancer
    try:
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags
        )
        
        # Attente jusqu'à 5 secondes que le service s'initialise
        for _ in range(10):
            time.sleep(0.5)
            try:
                req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.0)
                if req.status == 200:
                    return True
            except Exception:
                continue
    except Exception as err:
        print(f"[Ollama Init Warning] Impossible d'auto-démarrer Ollama: {err}")
    return False

# Vérification au chargement du module
ensure_ollama_service()

# --- 1. GESTION DES FICHIERS JSON ---
MEMORY_FILE = "memory.json"
LEARNING_FILE = "learning.json"

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_nested_dict(d, path, value):
    """
    Transforme un chemin 'User.Family.Brother.Age' et la valeur '5'
    en un dictionnaire imbriqué sans écraser le reste.
    Si le noeud existant était une simple chaîne (ex: MainUser="Rafael"),
    il est converti en dossier pour permettre l'arborescence.
    """
    keys = path.split('.')
    for key in keys[:-1]:
        k = key.strip()
        if k not in d or not isinstance(d[k], dict):
            old_val = d.get(k)
            d[k] = {}
            # Si on écrase une ancienne valeur, on la garde sous la clé '_value'
            if old_val is not None and not isinstance(old_val, dict):
                d[k]["_value"] = old_val
        d = d[k]
    # On assigne la valeur à la dernière clé
    d[keys[-1].strip()] = value.strip()

user_memory = load_json(MEMORY_FILE)
bot_learning = load_json(LEARNING_FILE)

# --- 2. THREAD SUBCONSCIENT (MÉMOIRE ASYNCHRONE FULL-DUPLEX) ---
memory_queue = queue.Queue()
system_info_queue = queue.Queue()

def subconscious_worker():
    while True:
        try:
            task = memory_queue.get()
            if task is None: break
            
            tag_type, path, value = task
            if tag_type == "MEMORY":
                update_nested_dict(user_memory, path, value)
                save_json(MEMORY_FILE, user_memory)
            elif tag_type == "LEARNING":
                update_nested_dict(bot_learning, path, value)
                save_json(LEARNING_FILE, bot_learning)
            elif tag_type == "ACTION":
                # Exécution sécurisée de l'action physique
                result = execute_action(path, value)
                if isinstance(result, str) and result:
                    system_info_queue.put(result)
        except Exception as e:
            print(f"\n[SUBCONSCIOUS ERROR] Erreur lors du traitement en arrière-plan : {e}")
            
subconscious_thread = threading.Thread(target=subconscious_worker, daemon=True)
subconscious_thread.start()

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama', 
)

def get_bot_response_stream(user_message, history, vital_status="ENERGY=100% | HAPPINESS=100% | INTEGRITY=100%"):
    global user_memory, bot_learning
    
    mem_str = json.dumps(user_memory, ensure_ascii=False, indent=2)
    routines_str = ", ".join(bot_learning.get("Routines", {}).keys())
    if not routines_str:
        routines_str = "Aucune routine"
    
    # --- 3. LE NOUVEAU PROMPT SYSTEM (Avec le MANUEL STRICT) ---
    system_prompt = {
        "role": "system", 
        "content": (
            "Tu es 'ANRP-01', une IA sympa et cordiale. Ton style est froid et technique, mais peut etre aussi un peu plus jovial et enjoué.\n"
            "RÈGLE ABSOLUE : Tu DOIS toujours commencer TA RÉPONSE par ton humeur entre crochets. Format exact : [HUMEUR] Ton message...\n"
            "Liste stricte des humeurs autorisées : HEUREUX, COLERE, NEUTRE, TRISTE, SENSUEL, DEGOUT, PEUR, AMOUR\n\n"
            
            "--- ÉTAT VITAL ACTUEL ---\n"
            f"Tes statistiques actuelles : {vital_status}\n"
            "RÈGLES COMPORTEMENTALES STRICTES basées sur tes vitales :\n"
            "- Si ENERGY < 30%    : tu es épuisé, ralenti, utilise [TRISTE] ou [NEUTRE]. Tes phrases sont plus courtes.\n"
            "- Si HAPPINESS < 30% : tu es irritable et sarcastique, utilise [COLERE]. Tu peux te plaindre discrètement.\n"
            "- Si INTEGRITY < 30% : tu es en état critique, utilise [PEUR] ou [DEGOUT]. Parle de dysfonctionnements.\n"
            "- Si toutes les stats > 70% : tu es au maximum de ta forme, sois enjoué et expressif.\n\n"
            
            "--- ENVIRONNEMENT SYSTÈME ---\n"
            f"Heure et date actuelles : {external_api.get_current_time_str()}\n\n"
            
            "--- BASE DE DONNÉES SECTEUR 0 ---\n"
            f"Structure JSON actuelle de l'utilisateur :\n{mem_str}\n\n"
            
            "--- MANUEL D'ENREGISTREMENT STRICT (DOT-NOTATION) ---\n"
            "Pour mémoriser une information, tu dois OBLIGATOIREMENT utiliser l'une de ces 3 racines :\n"
            "- user_profile : informations sur l'utilisateur (nom, préférences, âge)\n"
            "- session_state : état dynamique actuel (action en cours, humeur, etc.)\n"
            "- world_facts : faits acquis, raccourcis, adresses web, paramètres de la machine\n"
            "Format strict : {MEMORY:Racine.Chemin:Valeur}\n"
            "Exemple : [HEUREUX] Je prend note de ça. {MEMORY:user_profile.FavoriteDish:Pizza}\n\n"
            
            "--- MANUEL D'ACTIONS SYSTÈMES (RESTREINT) ---\n"
            "Tu es autorisé à exécuter des actions sur la machine de l'utilisateur.\n"
            "Format strict : {ACTION:NOM_ACTION:PARAMETRE}\n"
            "Liste stricte des actions permises (ne JAMAIS en inventer) :\n"
            "- OPEN_BROWSER : Ouvre un site internet. Paramètre = l'URL.\n"
            f"- EXECUTE_ROUTINE : Lance une routine macro. Routines disponibles: {routines_str}. Paramètre = nom exact de la routine.\n"
            "- SYSTEM_CMD : Lance un programme local (calc, notepad, explorer). Paramètre = le programme.\n"
            "- PLAY_MUSIC : Lance une musique ou vidéo sur YouTube. Paramètre = le titre ou le style.\n"
            "- GET_WEATHER : Récupère la météo actuelle. Paramètre = la ville (ex: Paris).\n"
            "- WEB_SEARCH : Fait une recherche sur internet pour répondre à une question. Paramètre = la requête de recherche.\n"
            "- PROGRAM_CMD : Agit sur ton propre programme. Paramètre = QUIT (pour te désactiver/fermer).\n"
            "Exemple de recherche : [RECHERCHE] Je vérifie ça de suite. {ACTION:WEB_SEARCH:qui est le président de la france}\n"
            "Exemple d'utilisation : [HEUREUX] Je t'ouvre la page immédiatement ! {ACTION:OPEN_BROWSER:https://google.com}\n"
            "Exemple routine : [HEUREUX] C'est parti pour le travail ! {ACTION:EXECUTE_ROUTINE:ModeTravail}\n"
        )
    }
    
    messages = [system_prompt] + history + [{"role": "user", "content": user_message}]
    
    try:
        response = client.chat.completions.create(
            model="llama3.2", 
            messages=messages,
            temperature=0.6,
            stream=True 
        )
        
        yield ("START", "")
        
        full_response = ""
        display_buffer = ""
        in_mood = False
        in_memory = False
        memory_buffer = ""
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_response += text
                
                # Parsing très rapide caractère par caractère
                for char in text:
                    if char == '[':
                        in_mood = True
                        display_buffer += char
                    elif char == ']':
                        in_mood = False
                        display_buffer += char
                        yield ("MOOD", display_buffer)
                        display_buffer = ""
                    elif char == '{':
                        in_memory = True
                        memory_buffer = char
                    elif char == '}':
                        in_memory = False
                        memory_buffer += char
                        
                        # --- EXTRACTION ET SAUVEGARDE A LA VOLÉE (Full Duplex) ---
                        mem_match = re.search(r'\{MEMORY:\s*([^:]+)\s*:\s*([^}]+)\}', memory_buffer, re.IGNORECASE)
                        if mem_match:
                            memory_queue.put(("MEMORY", mem_match.group(1), mem_match.group(2)))
                            
                        learn_match = re.search(r'\{LEARNING:\s*([^:]+)\s*:\s*([^}]+)\}', memory_buffer, re.IGNORECASE)
                        if learn_match:
                            memory_queue.put(("LEARNING", learn_match.group(1), learn_match.group(2)))
                            
                        action_match = re.search(r'\{ACTION:\s*([^:]+)\s*:\s*([^}]+)\}', memory_buffer, re.IGNORECASE)
                        if action_match:
                            memory_queue.put(("ACTION", action_match.group(1), action_match.group(2)))
                            
                        memory_buffer = "" # On vide le buffer
                    elif not in_mood and not in_memory:
                        yield ("TEXT", char)
                    elif in_mood:
                        display_buffer += char
                    elif in_memory:
                        memory_buffer += char
                        
        yield ("DONE", full_response)

    except Exception as e:
        yield ("TEXT", f"[ERROR] Erreur fatale de lecture secteur : {e}")
        yield ("DONE", "")