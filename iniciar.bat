@echo off
title Recadastramento de Base — Servidor
color 0A

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║      Recadastramento de Base v1.0        ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Verificar se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo  [ERRO] Ambiente virtual não encontrado.
    echo         Execute setup.bat primeiro.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo  Iniciando servidor na porta 5000...
echo.
echo  Acesse: http://localhost:5000
echo  Login padrão: Admin / Lamoia123
echo.
echo  (Pressione CTRL+C para encerrar)
echo  ══════════════════════════════════════════
echo.

:: Abre o navegador após 2 segundos
start /b cmd /c "timeout /t 2 >nul && start http://localhost:5000"

python app.py

pause
