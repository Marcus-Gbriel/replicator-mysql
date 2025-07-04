# Configuração de Exemplo - MySQL/MariaDB Structure Replicator

## Exemplo de Configuração de Conexão

### Banco de Origem (Teste/Desenvolvimento)
- **Host**: localhost ou IP do servidor
- **Porta**: 3306 (padrão MySQL/MariaDB)
- **Usuário**: usuario_teste
- **Senha**: senha_segura
- **Banco**: database_teste

### Banco de Destino (Produção)
- **Host**: servidor-producao.exemplo.com
- **Porta**: 3306
- **Usuário**: usuario_producao
- **Senha**: senha_muito_segura
- **Banco**: database_producao

## Permissões Necessárias

O usuário do banco de dados deve ter as seguintes permissões:

```sql
-- Para análise de estrutura
GRANT SELECT ON information_schema.* TO 'usuario'@'%';

-- Para modificação de estrutura
GRANT CREATE, ALTER, DROP, INDEX ON database_name.* TO 'usuario'@'%';

-- Para backup (se usar mysqldump)
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON database_name.* TO 'usuario'@'%';
```

## Recursos de Segurança

1. **Backup Automático**: Sempre criado antes de qualquer modificação
2. **Transações**: Todas as operações são executadas em transações
3. **Validação**: Conexões e estruturas são validadas antes da execução
4. **Logs Detalhados**: Todas as operações são registradas
5. **Criptografia**: Senhas são armazenadas de forma criptografada

## Limitações e Avisos

- ⚠️ **IMPORTANTE**: Este software modifica apenas a ESTRUTURA dos bancos
- ⚠️ **DADOS**: Nenhum dado é copiado, movido ou alterado
- ⚠️ **BACKUP**: Sempre mantenha backups atualizados dos bancos de produção
- ⚠️ **TESTE**: Teste sempre em ambiente de desenvolvimento primeiro

## Tipos de Alterações Suportadas

✅ **Suportado**:
- Criação de novas tabelas
- Adição de colunas (mantendo posição)
- Modificação de tipo de colunas
- Alteração de propriedades de colunas (NULL/NOT NULL, DEFAULT, etc.)
- Adição/modificação de comentários

⚠️ **Parcialmente Suportado**:
- Índices (detectados mas não replicados automaticamente)
- Chaves estrangeiras (detectadas mas não replicadas automaticamente)

❌ **Não Suportado**:
- Remoção de colunas (por segurança)
- Remoção de tabelas (por segurança)
- Procedures e Functions
- Views
- Triggers

## Solução de Problemas

### Erro de Conexão
1. Verifique se o servidor MySQL/MariaDB está rodando
2. Confirme host, porta, usuário e senha
3. Verifique se o firewall permite a conexão
4. Teste com client MySQL: `mysql -h host -P porta -u usuario -p`

### Erro de Permissão
1. Verifique se o usuário tem as permissões necessárias
2. Execute: `SHOW GRANTS FOR 'usuario'@'host';`

### Erro no Backup
1. Certifique-se de que mysqldump está instalado
2. Verifique se há espaço em disco suficiente
3. Confirme permissões de escrita na pasta backups/

### Logs para Diagnóstico
- Os logs são salvos em: `logs/replicator_YYYY-MM-DD.log`
- Use a opção "Visualizar Logs" no menu principal
