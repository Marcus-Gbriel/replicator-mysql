# Manual do Usuário - MySQL/MariaDB Structure Replicator

## 🎯 Visão Geral

O **MySQL/MariaDB Structure Replicator** é uma ferramenta segura e confiável para replicar estruturas de banco de dados entre ambientes MySQL/MariaDB. A aplicação foi desenvolvida especificamente para sincronizar estruturas entre bancos de teste e produção, **sem alterar dados existentes**.

## 🚀 Instalação Rápida

### Windows
1. Baixe e extraia os arquivos do projeto
2. Execute `install.bat` como administrador
3. Execute `run.bat` para iniciar a aplicação

### Linux/Mac
1. Baixe e extraia os arquivos do projeto
2. Execute `chmod +x install.sh run.sh`
3. Execute `./install.sh`
4. Execute `./run.sh` para iniciar a aplicação

### Instalação Manual
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Verificar ambiente
python check_environment.py

# 3. Executar aplicação
python main.py
```

## 📋 Pré-requisitos

### Software Necessário
- **Python 3.7+** (recomendado 3.8 ou superior)
- **MySQL/MariaDB** 5.7 ou superior
- **Conexão de rede** com os bancos de dados

### Opcional (Recomendado)
- **MySQL Client** para funcionalidades avançadas
- **mysqldump** para backups otimizados

### Permissões de Banco
O usuário deve ter as seguintes permissões:

```sql
-- ✅ OBRIGATÓRIO: Para análise de estrutura
GRANT SELECT ON information_schema.* TO 'usuario'@'host';

-- ✅ OBRIGATÓRIO: Para modificar estrutura
GRANT CREATE, ALTER, INDEX ON nome_do_banco.* TO 'usuario'@'host';

-- 🔧 RECOMENDADO: Para backups completos
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON nome_do_banco.* TO 'usuario'@'host';
```

## 🎮 Guia de Uso

### Primeira Execução

1. **Iniciar a Aplicação**
   ```bash
   python main.py
   ```

2. **Configurar Conexões** (Opção 1)
   - Configure primeiro o **Banco de Origem** (teste/desenvolvimento)
   - Configure depois o **Banco de Destino** (produção)

3. **Testar Conexões** (Opção 2)
   - Verifique se ambas as conexões estão funcionando

### Configuração de Conexões

#### Banco de Origem (Teste)
Este é o banco onde você fez as alterações de estrutura que deseja replicar.

**Exemplo:**
- **Nome da conexão:** Desenvolvimento
- **Host:** localhost (ou IP do servidor)
- **Porta:** 3306
- **Usuário:** dev_user
- **Senha:** [sua senha]
- **Banco:** projeto_dev

#### Banco de Destino (Produção)
Este é o banco que receberá as alterações de estrutura.

**Exemplo:**
- **Nome da conexão:** Produção
- **Host:** servidor-prod.empresa.com
- **Porta:** 3306
- **Usuário:** prod_user
- **Senha:** [sua senha segura]
- **Banco:** projeto_prod

### Processo de Replicação

#### 1. Análise de Estruturas (Opção 3)
- Compara as estruturas dos dois bancos
- Mostra diferenças encontradas
- **Não executa** nenhuma alteração

#### 2. Replicação (Opção 4)
**⚠️ PROCESSO SEGURO AUTOMÁTICO:**

1. **Validação:** Testa ambas as conexões
2. **Backup:** Cria backup completo do banco de destino
3. **Análise:** Compara estruturas detalhadamente
4. **Execução:** Aplica alterações em transação única
5. **Validação:** Confirma que a replicação foi bem-sucedida

## ✅ Operações Suportadas

### ✅ O que a aplicação FAZ:
- ✅ **Cria tabelas novas** no destino
- ✅ **Adiciona colunas** preservando posição
- ✅ **Modifica tipos de colunas** existentes
- ✅ **Altera propriedades** (NULL/NOT NULL, DEFAULT, etc.)
- ✅ **Mantém ordem original** das colunas
- ✅ **Cria backups automáticos** antes de qualquer alteração
- ✅ **Registra logs detalhados** de todas as operações

### ❌ O que a aplicação NÃO FAZ (por segurança):
- ❌ **NÃO remove** colunas ou tabelas
- ❌ **NÃO modifica** dados existentes
- ❌ **NÃO copia** dados entre bancos
- ❌ **NÃO remove** índices ou constraints
- ❌ **NÃO replica** procedures, functions, views ou triggers

## 📊 Exemplos Práticos

### Cenário 1: Adição de Nova Coluna
**Situação:** Você adicionou uma coluna `email` na tabela `usuarios` no banco de desenvolvimento.

**Processo:**
1. Configure as conexões (desenvolvimento → produção)
2. Execute "Analisar Estruturas" para ver a diferença
3. Execute "Replicar Estrutura"
4. A coluna será adicionada na mesma posição no banco de produção

### Cenário 2: Modificação de Tipo de Coluna
**Situação:** Você alterou o campo `telefone` de `VARCHAR(10)` para `VARCHAR(15)`.

**Processo:**
1. A análise detectará a modificação
2. A replicação aplicará `ALTER TABLE usuarios MODIFY COLUMN telefone VARCHAR(15)`
3. Dados existentes serão preservados

### Cenário 3: Nova Tabela
**Situação:** Você criou uma nova tabela `categorias` no desenvolvimento.

**Processo:**
1. A análise mostrará a tabela como "nova"
2. A replicação criará a tabela completa no destino
3. Estrutura idêntica será replicada

## 🔍 Monitoramento e Logs

### Visualizar Logs (Opção 5)
- Mostra as últimas operações
- Inclui timestamps detalhados
- Códigos de cores para facilitar leitura

### Arquivos de Log
- **Localização:** `logs/replicator_YYYY-MM-DD.log`
- **Conteúdo:** Todas as operações, erros e eventos de segurança
- **Rotação:** Um arquivo por dia

### Gerenciar Backups (Opção 6)
- **Listar backups:** Ver todos os backups criados
- **Criar backup manual:** Fazer backup sob demanda
- **Localização:** `backups/backup_BANCODB_YYYYMMDD_HHMMSS.sql`

## 🔧 Solução de Problemas

### Problema: "Erro de Conexão"
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```
**Soluções:**
1. Verifique se o MySQL/MariaDB está rodando
2. Confirme host, porta e credenciais
3. Teste firewall: `telnet host porta`
4. Teste com cliente MySQL: `mysql -h host -P porta -u usuario -p`

### Problema: "Permissão Negada"
```
Access denied for user 'usuario'@'host'
```
**Soluções:**
1. Verifique usuário e senha
2. Confirme permissões: `SHOW GRANTS FOR 'usuario'@'host';`
3. Contate o administrador do banco

### Problema: "Dependências Ausentes"
```
ModuleNotFoundError: No module named 'pymysql'
```
**Soluções:**
1. Execute: `pip install -r requirements.txt`
2. Verifique Python: `python --version`
3. Use o script: `install.bat` (Windows) ou `./install.sh` (Linux/Mac)

### Problema: "Backup Falhou"
```
mysqldump: command not found
```
**Soluções:**
1. Instale MySQL client: `apt install mysql-client` (Ubuntu)
2. A aplicação usará backup Python automaticamente
3. Funcionalidade não será prejudicada

## 🛡️ Segurança e Boas Práticas

### Antes de Usar em Produção
1. **✅ SEMPRE teste** em ambiente de desenvolvimento primeiro
2. **✅ Confirme** que você tem backup completo do banco de produção
3. **✅ Verifique** permissões limitadas do usuário
4. **✅ Execute** durante horário de baixo tráfego

### Durante a Operação
1. **✅ Monitore** os logs em tempo real
2. **✅ Não interrompa** o processo uma vez iniciado
3. **✅ Aguarde** a confirmação de sucesso
4. **✅ Valide** o resultado após a operação

### Após a Operação
1. **✅ Teste** a aplicação no banco atualizado
2. **✅ Mantenha** o backup criado automaticamente
3. **✅ Documente** as alterações realizadas
4. **✅ Monitore** a aplicação em produção

## 📞 Suporte e Ajuda

### Em Caso de Problemas
1. **Primeiro:** Consulte os logs da aplicação
2. **Segundo:** Execute `python check_environment.py`
3. **Terceiro:** Verifique esta documentação
4. **Último:** Contacte o suporte técnico

### Informações Úteis para Suporte
- Versão do Python: `python --version`
- Sistema operacional
- Versão do MySQL/MariaDB
- Arquivo de log completo
- Mensagem de erro exata

## 🔄 Fluxo Recomendado

### Para Alterações Rotineiras
```
1. Desenvolvimento → Fazer alterações
2. Testar → Validar funcionalidade  
3. Replicator → Analisar diferenças
4. Validar → Revisar alterações
5. Replicator → Executar replicação
6. Produção → Testar resultado
```

### Para Alterações Críticas
```
1. Planejamento → Documentar alterações
2. Backup Manual → Criar backup adicional
3. Janela de Manutenção → Agendar horário
4. Replicação → Executar processo
5. Validação → Testes extensivos
6. Rollback → Procedimento de contingência (se necessário)
```

## 📈 Dicas de Performance

### Para Bancos Grandes
- Execute durante horários de baixo tráfego
- Monitore espaço em disco para backups
- Consider fazer backup manual adicional

### Para Múltiplas Alterações
- Agrupe alterações em uma única sessão
- Documente todas as mudanças
- Teste cada alteração individualmente primeiro

## ⚡ Atalhos e Dicas

### Navegação Rápida
- **Opção 1 → 1:** Banco de origem
- **Opção 1 → 2:** Banco de destino  
- **Opção 3:** Análise rápida
- **Opção 4:** Replicação completa

### Comandos Úteis
```bash
# Verificar ambiente
python check_environment.py

# Executar testes
python tests/test_replicator.py

# Ver logs recentes
tail -f logs/replicator_$(date +%Y-%m-%d).log
```

---

**✨ Lembre-se:** Esta ferramenta foi projetada para ser segura e confiável. Sempre que houver dúvida, ela escolherá a opção mais segura, criando backups e registrando tudo em logs detalhados.
