# 🌌 UNIT-95 (ANRP-1) — Vision, Philosophie & Roadmap Long Terme

> *"Un esprit numérique rétro-futuriste, 100% libre, vivant localement sur votre bureau."*

---

## 🎯 1. La Vision : Pourquoi UNIT-95 est Unique

À l'heure où l'intelligence artificielle est dominée par des interfaces web froides, génériques et enfermées derrière des abonnements cloud payants, **UNIT-95 prend le chemin inverse** :

1. **Une Identité Visuelle & Émotionnelle Forte** : 
   Inspiré des terminaux cyberpunk, de *Fallout (RobCo)*, de *Portal (GLaDOS)* et du phénomène *Pwnagotchi*, UNIT-95 n'est pas un simple champ de texte : c'est une entité dotée d'expressions ASCII dynamiques, d'yeux qui clignent, d'états d'âme en temps réel et d'une mémoire persistante.

2. **100% Local, Privé et Gratuit à Vie** : 
   Aucune donnée personnelle n'est envoyée à des serveurs tiers. Tout tourne sur la machine de l'utilisateur grâce aux LLMs locaux (Ollama / `llama3.2`), éliminant tout coût d'API.

3. **Compagnon d'OS et Outil de Productivité** :
   Au-delà du dialogue, UNIT-95 agit directement : il lance des musiques, extrait l'information du web en temps réel (Mini-RAG), pilote des programmes et apprend des habitudes de son utilisateur.

---

## 🤝 2. Philosophie Open-Source, Mérite & Partage

Le projet fait le choix d'un **Open-Source éthique et communautaire** :

* **Fierté du Partage** : Permettre à n'importe quel passionné, étudiant ou développeur à travers le monde de monter son propre compagnon virtuel sans barrière technique ni financière.
* **Protection du Travail & Attribution** : Le projet est protégé sous licence **GPL v3 / Non-Commercial**. Quiconque utilise, modifie ou enrichit le code doit **citer le créateur original (Rafael / ANRP-1)** et conserver le code source ouvert et gratuit. Aucune commercialisation fermée ou privatisation du cœur du projet n'est permise sans accord.
* **Une Vitrine Technique & Communautaire** : Devenir une référence de projet complet alliant IA locale, infographie rétro, RAG léger et robotique logicielle.

---

## 🧩 3. Écosystème Modulaire : "Hackable par Nature"

Pour susciter un engouement communautaire fort, UNIT-95 est conçu pour être facilement étendu :

* 🎭 **Skins & Expressions (`faces/`)** : N'importe qui peut concevoir et partager de nouvelles expressions faciales en ASCII Art ou thèmes graphiques (Matrix, Amber CRT, Cyberpunk Neon).
* ⚡ **Système de Plug-ins & Skills (`plugins/`)** : Permettre aux développeurs d'ajouter de nouvelles actions en quelques lignes de Python (ex: intégration Spotify, suivi de commits GitHub, contrôle domotique Home Assistant, cours crypto, flux Twitch).
* 🧠 **Mémoire Arborescente Découplée (`memory.json`)** : Un format d'échange universel pour que l'IA garde ses souvenirs d'une session à l'autre.

---

## 📟 4. Le Potentiel Hardware : Du PC au Vrai Compagnon Physique

L'un des plus grands potentiels à long terme de UNIT-95 est son incarnation en **objet physique de bureau (Cyberdeck / Desktop Companion)** :

```
       +------------------------------------+
       |  [O_O]  UNIT-95 v2.0               |
       |  --------------------------------  |
       |  > Météo : Paris 18°C              |
       |  > Musique : Lofi Beats en cours   |
       |  > Status : À l'écoute...          |
       +------------------------------------+
             \                        /
              \______________________/
              [ Boîtier 3D Vintage ]
              [ Raspberry Pi 5 inside]
```

* **Micro-Terminal Dédié** : Boîtier imprimé en 3D style rétro-computing avec un écran LCD/OLED de 5 à 7 pouces alimenté par un **Raspberry Pi 4 / 5**.
* **Présence Réelle** : Équipé d'un micro et haut-parleur pour la voix, et d'un capteur de mouvement (PIR) pour saluer l'utilisateur lorsqu'il s'assoit à son bureau.
* **Architecture Hybride** : Le Raspberry Pi affiche l'interface et le son sur le bureau, tout en pouvant déléguer les calculs lourds de l'IA au PC principal via le réseau local.

---

## 🗺️ 5. Feuille de Route Long Terme (Roadmap)

### 📍 Phase 1 : Cœur Logiciel & Stabilité *(En cours - V1.0)*
- [x] Interface Pygame-CE rétro avec animations de visage ASCII (clignements, regards, émotions).
- [x] Intégration LLM local ultra-rapide (Ollama / streaming temps réel).
- [x] Double terminal défilable (Chat + Panneau d'information système).
- [x] Deep Web Search & Mini-RAG multi-sources (`ddgs` + `BeautifulSoup4`).
- [x] Mémoire arborescente persistante (`memory.json`).
- [x] Lanceur d'installation automatisé en 1-clic (`LANCER_UNIT-95.bat`).

### 📍 Phase 2 : Voix & Autonomie *(V1.5)*
- [ ] **Voice-to-Voice Local** : Intégration de `faster-whisper` (écoute micro) et `piper-tts` (voix naturelle ultra-rapide sans latence).
- [ ] **Comportement Proactif** : L'IA peut prendre l'initiative de parler (rappels programmés, pauses, alertes météo ou système).
- [ ] **Système de Plug-ins Dynamiques** : Chargement à chaud de modules communautaires sans modifier le code source central.

### 📍 Phase 3 : Incarnation Physique & Écosystème *(V2.0)*
- [ ] Conception et publication des plans de modélisation 3D (fichiers `.STL` pour imprimante 3D).
- [ ] Portabilité optimisée pour Raspberry Pi OS / Linux ARM64.
- [ ] Mode "Desk Station" avec capteur de présence et veille automatique.
- [ ] Création d'un hub communautaire (partage de skins de visages et de routines).

---

*Projet créé avec passion par Rafael — UNIT-95 est libre, modulaire et conçu pour grandir avec sa communauté.*
