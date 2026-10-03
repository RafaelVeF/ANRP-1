@echo off
chcp 65001 > nul
title UNIT-95 - Initialisation & Lancement

echo =======================================================
echo           INITIALISATION DE UNIT-95 (ANRP-1)
echo =======================================================
echo.

:: 1. Vérification de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'a pas ete detecte sur votre machine.
    echo Tentative d'installation automatique via winget...
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo [ERREUR] Impossible d'installer Python automatiquement.
        echo Veuillez telecharger et installer Python depuis : https://www.python.org/downloads/
        echo Pensez a cocher "Add Python to PATH" lors de l'installation.
        echo.
        pause
        exit /b
    )
    echo Python a ete installe avec succes. Veuillez relancer ce lanceur.
    pause
    exit /b
)

:: 2. Création et configuration du Venv (si inexistant)
if not exist ".venv" (
    echo [1/3] Creation de l'environnement virtuel (.venv)...
    python -m venv .venv
)

:: 3. Activation du Venv et installation des dépendances
echo [2/3] Verification des bibliotheques Python...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt --quiet --disable-pip-version-check
) else (
    python -m pip install -r requirements.txt --quiet --disable-pip-version-check
)

:: 4. Vérification d'Ollama & du Modèle IA
echo [3/3] Verification du modele IA local (llama3.2)...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ATTENTION] Ollama n'est pas detecte sur votre machine.
    echo UNIT-95 necessite Ollama pour son IA locale.
    echo Telechargement gratuit disponible sur : https://ollama.com
    echo.
) else (
    :: Téléchargement automatique du modèle s'il est manquant
    ollama list | findstr /i "llama3.2" >nul 2>&1
    if %errorlevel% neq 0 (
        echo Telechargement du modele IA 'llama3.2' en cours (patientez quelques instants)...
        ollama pull llama3.2
    )
)

echo.
echo =======================================================
echo               LANCEMENT DE UNIT-95 !
echo =======================================================
echo.

:: 5. Lancement de l'application principale
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [INFO] UNIT-95 s'est arrete.
    pause
)
