# MySQL/MariaDB Structure Replicator

## Descrição
Software seguro para replicação de estrutura de banco de dados MySQL/MariaDB entre ambientes de teste e produção.

## Funcionalidades
- Replicação segura de estrutura de tabelas
- Backup automático antes de operações
- Validação de conexões
- Log detalhado de operações
- Configuração via SQLite interno
- Preservação da ordem das colunas

## Instalação

1. Clone ou baixe o projeto
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

Execute o programa principal:
```bash
python main.py
```

## Estrutura do Projeto
- `main.py` - Arquivo principal
- `database/` - Módulos de banco de dados
- `config/` - Configurações
- `utils/` - Utilitários
- `logs/` - Arquivos de log

## Segurança
- Backup automático antes de qualquer operação
- Validação rigorosa de conexões
- Operações apenas na estrutura (não nos dados)
- Logs detalhados de todas as operações
