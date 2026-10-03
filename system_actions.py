import json
import webbrowser
import os
import subprocess
import urllib.parse
import external_api

ACTIONS_SPEC_FILE = "actions_spec.json"

def load_action_specs():
    """Charge les règles de sécurité depuis le fichier JSON."""
    if os.path.exists(ACTIONS_SPEC_FILE):
        with open(ACTIONS_SPEC_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_first_youtube_result(query):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Mode headless : on ne montre pas la navigation fantôme
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            encoded_query = urllib.parse.quote_plus(query)
            page.goto(f"https://www.youtube.com/results?search_query={encoded_query}")
            
            # Attendre que les vidéos régulières chargent (exclut souvent les pubs si on cible bien)
            page.wait_for_selector("ytd-video-renderer a#video-title", timeout=5000)
            
            first_video = page.locator("ytd-video-renderer a#video-title").first
            href = first_video.get_attribute("href")
            browser.close()
            
            if href:
                return f"https://www.youtube.com{href}"
    except Exception as e:
        print(f"[PLAYWRIGHT WARNING] Erreur ou non installé ({e}). Utilisation du Fallback.")
        pass
    
    # Fallback si playwright échoue
    encoded_query = urllib.parse.quote_plus(query)
    return f"https://www.youtube.com/results?search_query={encoded_query}"

def execute_action(action_name, param):
    """
    Exécute une action de manière sécurisée (Approche Whitelist).
    Bloque tout ce qui n'est pas explicitement autorisé dans actions_spec.json.
    """
    specs = load_action_specs()
    
    # 1. Vérification de Sécurité (Default Deny)
    action_name = action_name.strip().upper()
    action = specs.get(action_name)
    
    if not action or not action.get("enabled", False):
        print(f"\n[SECURITY BLOCK] Tentative d'exécution bloquée : {action_name} - {param}")
        return False
        
    # 2. Exécution des modules autorisés
    print(f"\n[SYSTEM ACTION] Exécution autorisée : {action_name} ({param})")
    
    if action_name == "OPEN_BROWSER":
        url = param.strip()
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return True
        
    elif action_name == "EXECUTE_ROUTINE":
        routine_name = param.strip()
        learning_data = {}
        if os.path.exists("learning.json"):
            try:
                with open("learning.json", 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
            except Exception:
                pass
                
        routines = learning_data.get("Routines", {})
        if routine_name in routines:
            print(f"[*] Démarrage de la routine : {routine_name}")
            actions = routines[routine_name]
            for act in actions:
                for k, v in act.items():
                    print(f"  -> Etape : {k} ({v})")
                    execute_action(k, v)
            return True
        else:
            print(f"[!] Routine introuvable : {routine_name}")
            return False
            
    elif action_name == "SYSTEM_CMD":
        cmd = param.strip().lower()
        safe_commands = {
            "calc": "calc.exe",
            "notepad": "notepad.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe"
        }
        if cmd in safe_commands:
            try:
                subprocess.Popen(safe_commands[cmd])
                return True
            except Exception as e:
                print(f"[!] Erreur de lancement de {cmd} : {e}")
                return False
        else:
            print(f"[!] Commande bloquée par la sécurité : {cmd}")
            return False

    elif action_name == "PROGRAM_CMD":
        cmd = param.strip().upper()
        if cmd == "QUIT":
            import pygame
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            print("[*] Ordre de fermeture reçu. Extinction de UNIT-95.")
            return True
        return False
    elif action_name == "PLAY_MUSIC":
        query = param.strip()
        url = get_first_youtube_result(query)
        webbrowser.open(url)
        return True
    
    elif action_name == "GET_WEATHER":
        city = param.strip()
        return external_api.get_weather(city)

    elif action_name == "WEB_SEARCH":
        query = param.strip()
        return external_api.search_web(query)

    return False
