

:: Verificar se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo  [ERRO] Ambiente virtual não encontrado.
    echo         Execute setup.bat primeiro.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat


python main.py

pause
