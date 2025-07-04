#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisador de estrutura de banco de dados
"""

import pymysql
from colorama import Fore, Style
from tabulate import tabulate

class StructureAnalyzer:
    def __init__(self, logger):
        """Inicializar analisador de estrutura"""
        self.logger = logger
    
    def analyze_database_structure(self, connection_details):
        """Analisar estrutura completa do banco de dados"""
        try:
            self.logger.operation_start(f"Análise da estrutura do banco {connection_details['database']}")
            
            connection = pymysql.connect(
                host=connection_details['host'],
                port=connection_details['port'],
                user=connection_details['username'],
                password=connection_details['password'],
                database=connection_details['database'],
                charset='utf8mb4'
            )
            
            structure = {
                'database': connection_details['database'],
                'tables': {},
                'connection_info': connection_details
            }
            
            with connection.cursor() as cursor:
                # Obter lista de tabelas
                self.logger.step(1, 3, "Obtendo lista de tabelas")
                cursor.execute("""
                    SELECT TABLE_NAME 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """, (connection_details['database'],))
                
                tables = cursor.fetchall()
                
                if not tables:
                    self.logger.warning(f"Nenhuma tabela encontrada no banco de dados '{connection_details['database']}'")
                    self.logger.info("Isso pode indicar:")
                    self.logger.info("- Banco de dados vazio")
                    self.logger.info("- Usuário sem permissão para ver tabelas")
                    self.logger.info("- Nome do banco incorreto")
                    
                    # Tentar verificar se o banco existe
                    cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s", (connection_details['database'],))
                    db_exists = cursor.fetchone()
                    if not db_exists:
                        self.logger.error(f"Banco de dados '{connection_details['database']}' não existe!")
                    
                    structure['tables'] = {}
                    connection.close()
                    self.logger.operation_end(f"Análise da estrutura do banco {connection_details['database']}", True)
                    return structure
                
                self.logger.info(f"Encontradas {len(tables)} tabelas")
                
                # Analisar cada tabela
                self.logger.step(2, 3, "Analisando estrutura das tabelas")
                for i, (table_name,) in enumerate(tables):
                    self.logger.info(f"Analisando tabela: {table_name}")
                    structure['tables'][table_name] = self._analyze_table_structure(cursor, connection_details['database'], table_name)
                
                # Analisar índices e chaves estrangeiras
                self.logger.step(3, 3, "Analisando índices e relacionamentos")
                for table_name in structure['tables']:
                    structure['tables'][table_name]['indexes'] = self._get_table_indexes(cursor, connection_details['database'], table_name)
                    structure['tables'][table_name]['foreign_keys'] = self._get_table_foreign_keys(cursor, connection_details['database'], table_name)
            
            connection.close()
            self.logger.operation_end(f"Análise da estrutura do banco {connection_details['database']}", True)
            return structure
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar estrutura do banco: {str(e)}")
            self.logger.operation_end(f"Análise da estrutura do banco {connection_details['database']}", False)
            return None
    
    def _analyze_table_structure(self, cursor, database_name, table_name):
        """Analisar estrutura de uma tabela específica"""
        table_info = {
            'columns': [],
            'primary_key': None,
            'auto_increment': None,
            'engine': None,
            'charset': None,
            'collation': None
        }
        
        # Obter informações das colunas com ordem preservada
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                ORDINAL_POSITION,
                COLUMN_DEFAULT,
                IS_NULLABLE,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                COLUMN_TYPE,
                COLUMN_KEY,
                EXTRA,
                COLUMN_COMMENT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """, (database_name, table_name))
        
        columns = cursor.fetchall()
        
        for column in columns:
            column_info = {
                'name': column[0],
                'position': column[1],
                'default': column[2],
                'nullable': column[3] == 'YES',
                'data_type': column[4],
                'max_length': column[5],
                'precision': column[6],
                'scale': column[7],
                'column_type': column[8],
                'key': column[9],
                'extra': column[10],
                'comment': column[11]
            }
            
            table_info['columns'].append(column_info)
            
            # Identificar chave primária
            if column[9] == 'PRI':
                table_info['primary_key'] = column[0]
            
            # Identificar auto increment
            if 'auto_increment' in column[10].lower():
                table_info['auto_increment'] = column[0]
        
        # Obter informações da tabela
        cursor.execute("""
            SELECT 
                ENGINE,
                TABLE_COLLATION,
                AUTO_INCREMENT
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """, (database_name, table_name))
        
        table_details = cursor.fetchone()
        if table_details:
            table_info['engine'] = table_details[0]
            table_info['collation'] = table_details[1]
            if table_details[1]:
                table_info['charset'] = table_details[1].split('_')[0]
        
        return table_info
    
    def _get_table_indexes(self, cursor, database_name, table_name):
        """Obter índices da tabela"""
        cursor.execute("""
            SELECT 
                INDEX_NAME,
                COLUMN_NAME,
                SEQ_IN_INDEX,
                NON_UNIQUE,
                INDEX_TYPE
            FROM information_schema.STATISTICS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """, (database_name, table_name))
        
        indexes = {}
        for row in cursor.fetchall():
            index_name = row[0]
            if index_name not in indexes:
                indexes[index_name] = {
                    'columns': [],
                    'unique': row[3] == 0,
                    'type': row[4]
                }
            indexes[index_name]['columns'].append(row[1])
        
        return indexes
    
    def _get_table_foreign_keys(self, cursor, database_name, table_name):
        """Obter chaves estrangeiras da tabela"""
        cursor.execute("""
            SELECT 
                kcu.CONSTRAINT_NAME,
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_SCHEMA,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME,
                rc.UPDATE_RULE,
                rc.DELETE_RULE
            FROM information_schema.KEY_COLUMN_USAGE kcu
            JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
                AND kcu.CONSTRAINT_SCHEMA = rc.CONSTRAINT_SCHEMA
            WHERE kcu.TABLE_SCHEMA = %s 
              AND kcu.TABLE_NAME = %s
              AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
              AND rc.CONSTRAINT_SCHEMA = %s
            ORDER BY kcu.CONSTRAINT_NAME
        """, (database_name, table_name, database_name))
        
        foreign_keys = {}
        for row in cursor.fetchall():
            fk_name = row[0]
            foreign_keys[fk_name] = {
                'column': row[1],
                'referenced_schema': row[2],
                'referenced_table': row[3],
                'referenced_column': row[4],
                'update_rule': row[5],
                'delete_rule': row[6]
            }
        
        return foreign_keys
    
    def compare_structures(self, source_structure, target_structure):
        """Comparar duas estruturas de banco de dados"""
        self.logger.operation_start("Comparação de estruturas")
        
        differences = {
            'new_tables': [],
            'missing_tables': [],
            'modified_tables': {},
            'identical_tables': []
        }
        
        # Verificar se as estruturas são válidas
        if not source_structure or not source_structure.get('tables'):
            self.logger.error("Estrutura do banco de origem está vazia ou inválida")
            return differences
        
        if not target_structure or not target_structure.get('tables'):
            self.logger.warning("Estrutura do banco de destino está vazia - todas as tabelas serão criadas")
            differences['new_tables'] = list(source_structure['tables'].keys())
            self.logger.operation_end("Comparação de estruturas", True)
            return differences
        
        source_tables = set(source_structure['tables'].keys())
        target_tables = set(target_structure['tables'].keys())
        
        # Tabelas novas (existem na origem mas não no destino)
        differences['new_tables'] = list(source_tables - target_tables)
        
        # Tabelas removidas (existem no destino mas não na origem)
        differences['missing_tables'] = list(target_tables - source_tables)
        
        # Tabelas comuns - verificar diferenças
        common_tables = source_tables & target_tables
        
        for table_name in common_tables:
            table_diff = self._compare_table_structures(
                source_structure['tables'][table_name],
                target_structure['tables'][table_name]
            )
            
            if table_diff['has_differences']:
                differences['modified_tables'][table_name] = table_diff
            else:
                differences['identical_tables'].append(table_name)
        
        self.logger.operation_end("Comparação de estruturas", True)
        return differences
    
    def _compare_table_structures(self, source_table, target_table):
        """Comparar estrutura de duas tabelas"""
        diff = {
            'has_differences': False,
            'new_columns': [],
            'removed_columns': [],
            'modified_columns': [],
            'column_order_changed': False,
            'table_properties_changed': False
        }
        
        # Comparar colunas
        source_columns = {col['name']: col for col in source_table['columns']}
        target_columns = {col['name']: col for col in target_table['columns']}
        
        source_col_names = set(source_columns.keys())
        target_col_names = set(target_columns.keys())
        
        # Colunas novas
        diff['new_columns'] = list(source_col_names - target_col_names)
        
        # Colunas removidas
        diff['removed_columns'] = list(target_col_names - source_col_names)
        
        # Colunas modificadas
        common_columns = source_col_names & target_col_names
        for col_name in common_columns:
            if not self._columns_are_identical(source_columns[col_name], target_columns[col_name]):
                diff['modified_columns'].append({
                    'name': col_name,
                    'source': source_columns[col_name],
                    'target': target_columns[col_name]
                })
        
        # Verificar ordem das colunas
        source_order = [col['name'] for col in source_table['columns']]
        target_order = [col['name'] for col in target_table['columns']]
        
        # Para colunas comuns, verificar se a ordem mudou
        common_order_source = [col for col in source_order if col in common_columns]
        common_order_target = [col for col in target_order if col in common_columns]
        
        if common_order_source != common_order_target:
            diff['column_order_changed'] = True
        
        # Verificar propriedades da tabela
        if (source_table['engine'] != target_table['engine'] or
            source_table['charset'] != target_table['charset'] or
            source_table['collation'] != target_table['collation']):
            diff['table_properties_changed'] = True
        
        # Determinar se há diferenças
        diff['has_differences'] = (
            len(diff['new_columns']) > 0 or
            len(diff['removed_columns']) > 0 or
            len(diff['modified_columns']) > 0 or
            diff['column_order_changed'] or
            diff['table_properties_changed']
        )
        
        return diff
    
    def _normalize_default_value(self, default_value, column_type, nullable):
        """Normalizar valores default problemáticos"""
        if default_value is None:
            return 'NULL' if nullable else None
        
        # Converter valores problemáticos de timestamp/datetime
        if default_value in ['0000-00-00 00:00:00', '0000-00-00']:
            if 'timestamp' in column_type.lower() or 'datetime' in column_type.lower():
                return 'NULL' if nullable else None
        
        return default_value

    def _columns_are_identical(self, col1, col2):
        """Verificar se duas colunas são idênticas"""
        # Normalizar valores default para comparação
        default1 = self._normalize_default_value(col1['default'], col1['column_type'], col1['nullable'])
        default2 = self._normalize_default_value(col2['default'], col2['column_type'], col2['nullable'])
        
        # Comparar propriedades importantes
        return (
            col1['column_type'] == col2['column_type'] and
            col1['nullable'] == col2['nullable'] and
            default1 == default2 and
            col1['extra'] == col2['extra'] and
            col1['key'] == col2['key']
        )
    
    def display_differences(self, differences):
        """Exibir diferenças encontradas"""
        print(f"\n{Fore.GREEN}=== RELATÓRIO DE DIFERENÇAS DE ESTRUTURA ==={Style.RESET_ALL}")
        
        # Tabelas novas
        if differences['new_tables']:
            print(f"\n{Fore.CYAN}TABELAS NOVAS (existem na origem, não no destino):{Style.RESET_ALL}")
            for table in differences['new_tables']:
                print(f"  {Fore.GREEN}+ {table}{Style.RESET_ALL}")
        
        # Tabelas removidas
        if differences['missing_tables']:
            print(f"\n{Fore.YELLOW}TABELAS QUE SERÃO IGNORADAS (existem no destino, não na origem):{Style.RESET_ALL}")
            for table in differences['missing_tables']:
                print(f"  {Fore.YELLOW}- {table}{Style.RESET_ALL}")
        
        # Tabelas modificadas
        if differences['modified_tables']:
            print(f"\n{Fore.MAGENTA}TABELAS COM DIFERENÇAS:{Style.RESET_ALL}")
            for table_name, table_diff in differences['modified_tables'].items():
                print(f"\n  {Fore.MAGENTA}Tabela: {table_name}{Style.RESET_ALL}")
                
                if table_diff['new_columns']:
                    print(f"    {Fore.GREEN}Colunas novas: {', '.join(table_diff['new_columns'])}{Style.RESET_ALL}")
                
                if table_diff['removed_columns']:
                    print(f"    {Fore.RED}Colunas removidas: {', '.join(table_diff['removed_columns'])}{Style.RESET_ALL}")
                
                if table_diff['modified_columns']:
                    print(f"    {Fore.YELLOW}Colunas modificadas: {len(table_diff['modified_columns'])}{Style.RESET_ALL}")
                
                if table_diff['column_order_changed']:
                    print(f"    {Fore.CYAN}Ordem das colunas alterada{Style.RESET_ALL}")
                
                if table_diff['table_properties_changed']:
                    print(f"    {Fore.BLUE}Propriedades da tabela alteradas{Style.RESET_ALL}")
        
        # Tabelas idênticas
        if differences['identical_tables']:
            print(f"\n{Fore.GREEN}TABELAS IDÊNTICAS ({len(differences['identical_tables'])}):{Style.RESET_ALL}")
            for table in differences['identical_tables']:
                print(f"  {Fore.GREEN}✓ {table}{Style.RESET_ALL}")
        
        # Resumo
        total_changes = (len(differences['new_tables']) + 
                        len(differences['modified_tables']))
        
        print(f"\n{Fore.CYAN}=== RESUMO ==={Style.RESET_ALL}")
        print(f"Tabelas a serem criadas: {Fore.GREEN}{len(differences['new_tables'])}{Style.RESET_ALL}")
        print(f"Tabelas a serem modificadas: {Fore.YELLOW}{len(differences['modified_tables'])}{Style.RESET_ALL}")
        print(f"Tabelas idênticas: {Fore.GREEN}{len(differences['identical_tables'])}{Style.RESET_ALL}")
        print(f"Total de alterações necessárias: {Fore.CYAN}{total_changes}{Style.RESET_ALL}")
        
        if total_changes == 0:
            print(f"\n{Fore.GREEN}✓ As estruturas estão sincronizadas!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠ Replicação necessária para {total_changes} item(s){Style.RESET_ALL}")
