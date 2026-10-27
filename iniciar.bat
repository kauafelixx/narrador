@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Narrador local - Chatterbox V3
if not exist ".venv\Scripts\python.exe" (
    echo Ambiente Python nao encontrado. Consulte README.md para instalar.
    goto falha
)
call ".venv\Scripts\activate.bat"
set PYTHONUTF8=1
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set GRADIO_ANALYTICS_ENABLED=False
set HF_HUB_DISABLE_TELEMETRY=1
echo Verificando o ambiente local...
python scripts\verificar.py
if errorlevel 1 goto falha
echo.
echo Abrindo http://127.0.0.1:7860
echo Para encerrar a interface e liberar a GPU, pressione Ctrl+C nesta janela.
python app.py %*
if errorlevel 1 goto falha
exit /b 0
:falha
echo.
echo A inicializacao falhou. Leia a mensagem acima e consulte README.md e a pasta logs.
if not "%NARRADOR_SEM_PAUSA%"=="1" pause
exit /b 1
