@echo off
echo =======================================================
echo  MySQL/MariaDB Structure Replicator - Instalacao
echo =======================================================
echo.

echo Verificando se Python esta instalado...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado! Por favor, instale Python 3.7 ou superior.
    echo Baixe em: https://python.org/downloads/
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Verificando se pip esta disponivel...
pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: pip nao encontrado!
    pause
    exit /b 1
)

echo pip encontrado!
echo.

echo Instalando dependencias...
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo =======================================================
    echo  Instalacao concluida com sucesso!
    echo =======================================================
    echo.
    echo Para executar o programa, use:
    echo   python main.py
    echo.
    echo NOTA: Certifique-se de que o MySQL/MariaDB esta acessivel
    echo       e que voce tem as credenciais corretas.
    echo.
) else (
    echo.
    echo ERRO: Falha na instalacao das dependencias!
    echo Verifique sua conexao com a internet e tente novamente.
)

pause
