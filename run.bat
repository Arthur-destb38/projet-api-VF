@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: =============================================================================
:: Crypto Sentiment Dashboard - Script d'installation et de lancement (Windows)
:: =============================================================================

cd /d "%~dp0"

echo.
echo ══════════════════════════════════════════════════════════════
echo           Crypto Sentiment Dashboard - Setup
echo ══════════════════════════════════════════════════════════════
echo.

:: =============================================================================
:: 1. Vérifier Python
:: =============================================================================
echo [1/5] Verification de Python...

python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo [ERREUR] Python non trouve. Installez Python 3.10+
        pause
        exit /b 1
    )
    set PYTHON_CMD=python3
) else (
    set PYTHON_CMD=python
)

for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detecte

:: =============================================================================
:: 2. Créer le fichier .env si nécessaire
:: =============================================================================
echo [2/5] Configuration de l'environnement...

if not exist ".env" (
    echo Creation du fichier .env...
    (
        echo # =============================================================================
        echo # Configuration Crypto Sentiment Dashboard
        echo # =============================================================================
        echo.
        echo # Mot de passe pour acceder au dashboard ^(optionnel, laisser vide pour acces libre^)
        echo # APP_PASSWORD=votre_mot_de_passe
        echo.
        echo # Base de donnees PostgreSQL ^(optionnel, utilise SQLite par defaut^)
        echo # DATABASE_URL=postgresql://user:password@localhost:5432/crypto_sentiment
        echo.
        echo # =============================================================================
        echo # APIs ^(optionnel - pour les scrapers avances^)
        echo # =============================================================================
        echo.
        echo # Twitter/X
        echo # TWITTER_USERNAME=
        echo # TWITTER_PASSWORD=
        echo.
        echo # YouTube Data API
        echo # YOUTUBE_API_KEY=
        echo.
        echo # GitHub Personal Access Token
        echo # GITHUB_TOKEN=
        echo.
        echo # Bluesky
        echo # BLUESKY_HANDLE=
        echo # BLUESKY_APP_PASSWORD=
    ) > .env
    echo [OK] Fichier .env cree
) else (
    echo [OK] Fichier .env existant
)

:: =============================================================================
:: 3. Créer l'environnement virtuel
:: =============================================================================
echo [3/5] Configuration de l'environnement virtuel...

if not exist ".venv" (
    echo Creation du venv...
    %PYTHON_CMD% -m venv .venv
    echo [OK] Environnement virtuel cree
) else (
    echo [OK] Environnement virtuel existant
)

:: =============================================================================
:: 4. Installer les dépendances
:: =============================================================================
echo [4/5] Installation des dependances...

:: Upgrade pip
.venv\Scripts\pip install --upgrade pip -q

:: Vérifier si Poetry est disponible
where poetry >nul 2>&1
if not errorlevel 1 (
    echo Installation via Poetry...
    poetry install --no-interaction
) else (
    if exist ".venv\Scripts\poetry.exe" (
        echo Installation via Poetry ^(venv^)...
        .venv\Scripts\poetry install --no-interaction
    ) else (
        echo Installation via pip...
        .venv\Scripts\pip install -q streamlit pandas numpy plotly python-dotenv selenium beautifulsoup4 lxml requests transformers torch statsmodels undetected-chromedriver google-api-python-client psycopg2-binary instaloader atproto fastapi uvicorn jinja2
    )
)

echo [OK] Dependances installees

:: =============================================================================
:: 5. Lancer Streamlit
:: =============================================================================
echo [5/5] Lancement de l'application...

:: Trouver un port disponible
set PORT=8501

:check_port
netstat -an | find ":%PORT%" | find "LISTENING" >nul 2>&1
if not errorlevel 1 (
    set /a PORT+=1
    if %PORT% gtr 8600 (
        echo [ERREUR] Aucun port disponible entre 8501 et 8600
        pause
        exit /b 1
    )
    goto check_port
)

echo.
echo ══════════════════════════════════════════════════════════════
echo   Application prete !
echo.
echo   URL: http://localhost:%PORT%
echo.
echo   Appuyez sur Ctrl+C pour arreter
echo ══════════════════════════════════════════════════════════════
echo.

:: Lancer Streamlit
.venv\Scripts\python -m streamlit run streamlit_app.py --server.port %PORT%

pause
