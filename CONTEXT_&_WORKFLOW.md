# 🚀 PROJET ANTIGRAVITY - Master Spec & Roadmap

**Vision :** Créer un agent IA 100% local, ultra-rapide, doté d'une mémoire persistante, capable de manipuler le système d'exploitation et d'apprendre de ses erreurs, le tout déclenché instantanément par une touche physique.

**Principe fondamental (La Règle d'Or) :**
*Le LLM (2B/3B) ne fait pas le travail lourd. Il agit uniquement comme un "Routeur d'Intentions". Il lit le contexte, choisit une action et crache un JSON strict. C'est le moteur Python qui exécute l'action de manière déterministe.*

---

## 🧠 1. L'Architecture à 3 Couches

1. **L'Interface (Le Déclencheur) :** Remplacement de la touche Copilot matérielle (Win+Shift+F23) via un script AutoHotkey ou PowerToys pour lancer le script Python de manière invisible.
2. **Le Cerveau (Le Modèle Local) :** Modèle 2B ou 3B (ex: Llama-3.2-3B ou Qwen-2.5-3B) tournant via Ollama/llama.cpp. Sortie contrainte obligatoirement par une grammaire JSON (GBNF).
3. **Le Moteur (Python) :** L'orchestrateur central qui gère l'OS, pilote le navigateur (Playwright) et lit/écrit dans les fichiers JSON.

---

## 🗂️ 2. Le Cerveau Tripartite (Fichiers d'état)

Le système cognitif repose sur 3 piliers JSON :

### A. `ACTIONS.json` (Ce qu'il sait faire)
Un inventaire des capacités (Tool Calling) au format JSON Schema strict.
- `open_url(url)` : Ouvre le navigateur.
- `web_action(selector, action)` : Clic/Saisie via Playwright.
- `system_cmd(cmd)` : Lance un programme OS.

### B. `MEMORY.json` (Ce qu'il sait du monde et de la session)
Divisé en trois sous-catégories pour ne pas saturer le prompt :
1. **`user_profile`** : Statique (Nom, OS, préférences validées).
2. **`session_state`** : Dynamique (App active, dernière URL visitée, timestamp).
3. **`world_facts`** : Base de données des faits acquis au fil de l'eau.

### C. `LEARNS.json` (Le transformateur d'expérience)
La mémoire procédurale de l'agent.
- **Procédures composées :** Workflows fréquents (ex: "Routine de travail" = ferme Discord + ouvre Notion + met playlist Lofi).
- **Anti-patterns (Post-Mortem) :** Les erreurs qu'il a commises et la règle pour ne plus les refaire.
- **Code validé :** Les scripts Python qu'il a générés avec succès et qu'il peut réutiliser (Approche Voyager).

---

## 🛠️ 3. Fonctionnalités Avancées (Les "Super-Pouvoirs")

* **Contrôle Web Profond (Playwright/CDP) :** Ne clique pas "à l'aveugle" sur l'écran. Se connecte au DOM du navigateur pour injecter des actions précises (ex: `page.locator('video').click()`).
* **Boucle d'Auto-Correction de Code (Voyager-like) :** Génère du code ➔ L'exécute dans une sandbox locale (subprocess) ➔ Lit le Traceback/Stderr en cas d'erreur ➔ Se corrige tout seul ➔ Sauvegarde dans `LEARNS.json` quand ça marche.
* **Intégration Vocale Sans Latence (Local) :**
  - *Wake Word* : `openWakeWord` (Consommation CPU quasi-nulle, attend le mot "Antigravity").
  - *VAD (Voice Activity Detection)* : Détecte quand l'utilisateur arrête de parler.
  - *Transcription* : `faster-whisper` (Traduit l'audio en texte en <200ms sur GPU).

---

## ✅ 4. Check-list d'Implémentation (Roadmap)

### Phase 1 : La Fondation (V0.1 - "Hello World Local")
- [ ] Connecter le script Python à l'API locale d'Ollama.
- [ ] Implémenter le parseur de sortie (forcer le format JSON strict).
- [ ] Mapper la touche Copilot (AutoHotkey) vers le `.bat` lanceur.
- [ ] Faire en sorte que l'agent puisse ouvrir une URL simple (Action 1).
- [ ] Faire en sorte de pouvoir redimentionner la taille de l'agent pour que celui ci puisse s'executer dans une portion de l'ecran (coin, taille ajustable, tel une fenetre d'application)

### Phase 2 : Le Cerveau Tripartite (V0.5 - "L'Éveil")
- [ ] Créer la structure propre de `MEMORY.json` (Profil / Session / Faits).
- [ ] Créer `ACTIONS.json` au format JSON Schema pour le modèle.
- [ ] Coder la boucle de mise à jour de la mémoire : l'agent met à jour son état à chaque action.
- [ ] Mettre en place `LEARNS.json` (ajout manuel des premières routines pour tester).

### Phase 3 : Les Mains sur le Clavier (V1.0 - L'Assistant Utile)
- [ ] Intégrer Playwright pour l'automatisation web (navigation silencieuse, scraping de base).
- [ ] Coder le moteur de "Self-Debugging" (exécuter un script Python temp.py et récupérer les erreurs).
- [ ] Créer une interface minimaliste (Overlay / Popup Streamlit ou Flet) au lieu d'une simple console noire.
- [ ] Relier le modèle au net pour etre capable de récuperer des informations élémentaires (dates, température,news locales, sorties, météo)

### Phase 4 : L'Effet Waouh (V2.0 - Jarvis)
- [ ] Intégrer `openWakeWord` pour écouter le mot-clé (ex: "Antigravity").
- [ ] Intégrer `faster-whisper` pour transcrire la commande vocale.
- [ ] Relier la transcription vocale au flux existant (Voix -> Texte -> Prompt -> JSON -> Action).
- [ ] Packager l'application (`PyInstaller`) avec un installeur pour le partager aux amis.

---
*Projet Antigravity - Conçu pour tourner localement, pensé pour évoluer organiquement.*