#!/bin/bash

echo "======================================================="
echo "  MySQL/MariaDB Structure Replicator"
echo "======================================================="
echo

echo "Iniciando aplicação..."
python3 main.py

if [ $? -ne 0 ]; then
    echo
    echo "ERRO: Falha ao executar a aplicação!"
    echo
    echo "Possíveis causas:"
    echo "- Dependências não instaladas (execute ./install.sh)"
    echo "- Python3 não encontrado no PATH"
    echo "- Erro na aplicação (verifique os logs)"
    echo
fi
