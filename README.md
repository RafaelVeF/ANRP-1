## UNIT-95 (ANRP-1)

UNIT-95 est un assistant IA interactif local propulsé par une interface **Pygame-CE** rétro-futuriste, un moteur d'émotions dynamique (ASCII faces), un système de mémoire arborescente persistante, et un pipeline de recherche web en temps réel (Mini-RAG).

---

##  Fonctionnalités

-  **IA Locale Rapide & Privée** : Utilise Ollama (`llama3.2`) pour répondre instantanément sans dépendre d'une API payante.
-  **Visages ASCII Dynamiques** : Expressions et animations fluides en temps réel selon l'humeur de l'IA (clignements, réactions, émotions).
-  **Deep Web Search (Mini-RAG)** : Recherche web avancée avec crawling multi-thread (`ddgs`, `BeautifulSoup4`) et extraction de faits récents.
-  **Exécution d'Actions Système** : Lancement de musique YouTube, météo en direct, ouverture d'URLs, exécution de commandes locales.
-  **Mémoire Persistante & Apprentissage** : Retient les informations clés sur l'utilisateur au fil des discussions dans `memory.json`.
-  **Double Terminal Défilable** : Fenêtre de chat à gauche + panneau d'informations système et recherche à droite avec défilement fluide à la molette.

---

##  Démarrage Rapide (1-Clic)

### Pour les utilisateurs Windows :
1. Téléchargez ou clonez le projet.
2. Double-cliquez sur **`LANCER_UNIT-95.bat`**.
3. Le script s'occupe de **tout** automatiquement :
   - Vérification de Python.
   - Création de l'environnement virtuel (`.venv`).
   - Installation des dépendances nécessaires (`requirements.txt`).
   - Téléchargement du modèle IA local si besoin (`ollama pull llama3.2`).
   - Lancement de UNIT-95 !

---

##  Installation Manuelle (Optionnelle)

Si vous préférez installer manuellement les dépendances :

```bash
# 1. Cloner le projet
git clone https://github.com/RafaelVeF/ANRP-1.git
cd ANRP-1

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
python main.py
```

---

##  Dépendances Principales
- `pygame-ce` : Interface graphique et boucle d'événements.
- `openai` : Client de streaming local pour Ollama.
- `pyttsx3` : Synthèse vocale.
- `requests` & `beautifulsoup4` : Web scraping et extraction de texte.
- `ddgs` : Moteur de recherche web en temps réel.
