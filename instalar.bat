@echo off
echo ======================================================
echo  Sistema de Controle de Contratos - Instalacao
echo ======================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.10+ e tente novamente.
    pause
    exit /b 1
)

echo [1/3] Criando ambiente virtual...
python -m venv venv
if errorlevel 1 (
    echo [ERRO] Falha ao criar venv.
    pause
    exit /b 1
)

echo [2/3] Instalando dependencias...
call venv\Scripts\activate
pip install --upgrade pip -q
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo [3/3] Instalacao concluida!
echo.
echo Para iniciar o sistema execute: iniciar.bat
echo.
pause
