# Sistema de Sincronização de Dados Entre Ambientes

## Visão Geral

O novo sistema de sincronização de dados permite manter tabelas específicas sincronizadas entre ambientes (desenvolvimento, homologação e produção). Isso é essencial para tabelas de configuração, navegação, permissões e outras que devem estar consistentes entre os ambientes.

## Funcionalidades

### 📋 **Configuração de Tabelas**
- **Adicionar tabelas** para sincronização
- **Remover tabelas** da sincronização
- **Ativar/Desativar** tabelas específicas
- **Configurar colunas** individuais para sincronização

### 🔄 **Tipos de Sincronização**

#### 1. **Full (Completa)**
- Substitui todos os dados da tabela de destino
- Ideal para: tabelas de configuração, menus, permissões
- ⚠️ **Cuidado**: Remove todos os dados existentes

#### 2. **Incremental**
- Sincroniza apenas registros novos ou modificados
- Ideal para: tabelas que crescem constantemente
- 📈 **Performance**: Mais rápida para tabelas grandes

#### 3. **Key Only (Apenas Chaves)**
- Adiciona apenas registros que não existem no destino
- Ideal para: tabelas de referência, lookup tables
- 🔒 **Segurança**: Não remove dados existentes

### 🎯 **Direções de Sincronização**

- **Homologação → Produção**: Para promover configurações testadas
- **Produção → Homologação**: Para manter ambientes alinhados

## Como Usar

### 1. **Configurar Tabelas para Sincronização**

1. No menu principal, escolha **"6 - Sincronizar Dados"**
2. Selecione **"1 - Configurar Tabelas"**
3. Escolha **"1 - Adicionar Tabela"**
4. Siga os passos:
   - Digite o nome da tabela
   - Adicione uma descrição (opcional)
   - Escolha o tipo de sincronização
   - Defina a coluna de chave primária

**Exemplo de Configuração:**
```
Tabela: navigation_menus
Descrição: Menus de navegação do sistema
Tipo: Full (para substituir completamente)
Chave: menu_id
```

### 2. **Configurar Colunas Específicas**

1. No menu de sincronização, escolha **"3 - Configurar Colunas"**
2. Selecione a tabela desejada
3. Para cada coluna, defina:
   - **Sincronizar**: Sim/Não
   - **Direção**: both/to_prod/to_dev

**Exemplo:**
```
Tabela: users
- user_id: Sincronizar = Não (chave local)
- username: Sincronizar = Sim, Direção = both
- email: Sincronizar = Sim, Direção = both
- password: Sincronizar = Não (segurança)
```

### 3. **Executar Sincronização**

#### Sincronização Completa
1. Escolha **"4 - Sincronizar Dados"**
2. Selecione a direção (homologação→produção ou produção→homologação)
3. Confirme a operação

#### Sincronização de Tabela Específica
1. Escolha **"5 - Sincronizar Tabela"**
2. Selecione a tabela desejada
3. Selecione a direção
4. Confirme a operação

### 4. **Monitorar Histórico**

1. Escolha **"6 - Histórico"**
2. Visualize todas as sincronizações realizadas
3. Filtre por tabela específica (opcional)

## Casos de Uso Comuns

### 🎨 **Telas de Navegação**
```sql
Tabela: navigation_screens
Tipo: Full
Uso: Novas telas criadas em homologação precisam aparecer em produção
```

### 🔐 **Permissões de Sistema**
```sql
Tabela: system_permissions
Tipo: Key Only
Uso: Novas permissões criadas não devem sobrescrever configurações existentes
```

### 📊 **Configurações de Relatórios**
```sql
Tabela: report_configs
Tipo: Incremental
Uso: Novos relatórios e modificações devem ser sincronizados
```

### 🏢 **Dados de Agências**
```sql
Tabela: agencies
Tipo: Key Only
Uso: Novas agências criadas devem estar disponíveis em ambos ambientes
```

## Segurança e Boas Práticas

### 🔒 **Tabelas Críticas**
O sistema identifica automaticamente tabelas críticas que **NÃO** devem ser limpas completamente:
- `users` (usuários)
- `user_passwords` (senhas)
- `processes` (processos)
- `log_actions` (logs de ações)
- `log_requests` (logs de requisições)

### ✅ **Boas Práticas**

1. **Teste Primeiro**: Sempre teste em ambiente de desenvolvimento
2. **Backup Automático**: O sistema cria backup antes de qualquer alteração
3. **Monitore Logs**: Acompanhe o histórico de sincronizações
4. **Configure Gradualmente**: Comece com poucas tabelas e expanda
5. **Use Tipos Apropriados**: 
   - Full para tabelas pequenas de configuração
   - Incremental para tabelas que crescem
   - Key Only para tabelas de referência

### ⚠️ **Cuidados**

1. **Sincronização Full**: Remove TODOS os dados da tabela de destino
2. **Chaves Primárias**: Certifique-se de que as chaves primárias estão corretas
3. **Dependências**: Sincronize tabelas relacionadas na ordem correta
4. **Horários**: Execute sincronizações em horários de baixo movimento

## Estrutura de Dados

### 📊 **Configurações Armazenadas**

O sistema armazena as configurações em tabelas SQLite locais:

- `data_sync_tables`: Configurações das tabelas
- `data_sync_columns`: Configurações das colunas
- `data_sync_history`: Histórico de sincronizações

### 📈 **Relatórios Disponíveis**

- **Tabelas Configuradas**: Lista todas as tabelas e seus tipos
- **Histórico de Sincronização**: Mostra sucesso/erro de cada operação
- **Colunas por Tabela**: Detalha configuração de cada coluna

## Exemplo de Fluxo Completo

### Cenário: Adicionar nova tela de navegação

1. **Desenvolvimento**: Criar nova tela e menu
2. **Configurar**: Adicionar tabela `navigation_menus` para sincronização
3. **Testar**: Sincronizar dev → homologação
4. **Validar**: Verificar se a tela aparece corretamente
5. **Produção**: Sincronizar homologação → produção
6. **Monitorar**: Verificar histórico de sincronização

### Resultado
✅ Nova tela disponível em produção
✅ Dados mantidos consistentes
✅ Processo auditado e logado

## Suporte e Troubleshooting

### 🔍 **Problemas Comuns**

1. **Erro de Chave Primária**: Verificar se a coluna configurada existe
2. **Tabela Não Encontrada**: Confirmar se a tabela existe em ambos ambientes
3. **Permissão Negada**: Verificar permissões do usuário do banco
4. **Dados Inconsistentes**: Usar modo Key Only para evitar conflitos

### 📞 **Logs Detalhados**

Todos os processos são logados em:
- `logs/replicator_YYYY-MM-DD.log`
- Histórico na interface do sistema
- Configurações salvas em SQLite local

---

> **💡 Dica**: Comece configurando uma tabela simples como teste, como `system_config` ou `navigation_menus`, antes de configurar tabelas mais complexas.
