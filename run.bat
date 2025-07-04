@echo off
echo =======================================================
echo  MySQL/MariaDB Structure Replicator
echo =======================================================
echo.

echo Iniciando aplicacao...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo ERRO: Falha ao executar a aplicacao!
    echo.
    echo Possíveis causas:
    echo - Dependencias nao instaladas (execute install.bat)
    echo - Python nao encontrado no PATH
    echo - Erro na aplicacao (verifique os logs)
    echo.
)

pause
