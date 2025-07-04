#!/bin/bash

echo "======================================================="
echo "  MySQL/MariaDB Structure Replicator - Instalação"
echo "======================================================="
echo

echo "Verificando se Python está instalado..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não encontrado! Por favor, instale Python 3.7 ou superior."
    exit 1
fi

echo "Python encontrado!"
echo

echo "Verificando se pip está disponível..."
if ! command -v pip3 &> /dev/null; then
    echo "ERRO: pip3 não encontrado!"
    exit 1
fi

echo "pip encontrado!"
echo

echo "Instalando dependências..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo
    echo "======================================================="
    echo "  Instalação concluída com sucesso!"
    echo "======================================================="
    echo
    echo "Para executar o programa, use:"
    echo "  python3 main.py"
    echo
    echo "NOTA: Certifique-se de que o MySQL/MariaDB está acessível"
    echo "      e que você tem as credenciais corretas."
    echo
else
    echo
    echo "ERRO: Falha na instalação das dependências!"
    echo "Verifique sua conexão com a internet e tente novamente."
fi
