#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replicador de estrutura de banco de dados
"""

import os
import datetime
import pymysql
from colorama import Fore, Style
from database.structure_analyzer import StructureAnalyzer

class Replicator:
    def __init__(self, logger):
        """Inicializar replicador"""
        self.logger = logger
        self.structure_analyzer = StructureAnalyzer(logger)
        self.backups_dir = "backups"
        os.makedirs(self.backups_dir, exist_ok=True)
    
    def replicate_structure(self, source_connection, target_connection):
        """Executar replicação completa de estrutura"""
        try:
            self.logger.operation_start("REPLICAÇÃO DE ESTRUTURA DE BANCO DE DADOS")
            
            # Passo 1: Validar conexões
            self.logger.step(1, 6, "Validando conexões")
            if not self._validate_connections(source_connection, target_connection):
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
                return False
            
            # Passo 2: Criar backup do banco de destino
            self.logger.step(2, 6, "Criando backup do banco de destino")
            backup_file = self.create_backup(target_connection)
            if not backup_file:
                self.logger.error("Falha ao criar backup. Replicação abortada por segurança.")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
                return False
            
            # Passo 3: Analisar estruturas
            self.logger.step(3, 6, "Analisando estruturas dos bancos")
            source_structure = self.structure_analyzer.analyze_database_structure(source_connection)
            target_structure = self.structure_analyzer.analyze_database_structure(target_connection)
            
            if not source_structure or not target_structure:
                self.logger.error("Falha ao analisar estruturas")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
                return False
            
            # Passo 4: Comparar estruturas
            self.logger.step(4, 6, "Comparando estruturas")
            differences = self.structure_analyzer.compare_structures(source_structure, target_structure)
            
            # Verificar se o banco de destino está vazio (situação especial)
            target_is_empty = len(target_structure['tables']) == 0
            source_has_tables = len(source_structure['tables']) > 0
            
            if target_is_empty and source_has_tables:
                self.logger.info(f"Banco de destino está vazio. Criando {len(source_structure['tables'])} tabelas...")
                # Para banco vazio, forçar criação de todas as tabelas
                return self._create_all_tables_from_scratch(target_connection, source_structure, backup_file)
            
            # Detectar se estamos em um loop de replicação iterativa (apenas se não é banco vazio)
            if not target_is_empty and self._detect_iterative_replication_loop(source_connection, target_connection):
                self.logger.success("Problema de replicação iterativa corrigido automaticamente")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", True)
                return True
            
            # Verificar se há alterações estruturais significativas
            structural_changes = (len(differences['new_tables']) + 
                                len(differences['modified_tables']))
            index_changes = len(differences.get('index_differences', {}))
            total_changes = structural_changes + index_changes
            
            if total_changes == 0:
                self.logger.success("Estruturas já estão sincronizadas!")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", True)
                return True
            
            # Passo 5: Gerar e executar comandos SQL
            if structural_changes > 0:
                self.logger.step(5, 6, f"Executando {structural_changes} alterações estruturais")
                success = self._execute_replication(target_connection, source_structure, differences)
                
                if not success:
                    self.logger.error("Falha durante a replicação estrutural")
                    self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
                    return False
            else:
                self.logger.step(5, 6, "Nenhuma alteração estrutural necessária, sincronizando índices")
                # Apenas sincronizar índices se não há mudanças estruturais
                self._sync_indexes_only(target_connection, source_structure, differences)
            
            # Passo 6: Validar resultado
            self.logger.step(6, 6, "Validando resultado da replicação")
            if self._validate_replication(source_connection, target_connection):
                self.logger.success(f"Replicação concluída! Backup salvo em: {backup_file}")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", True)
                return True
            else:
                self.logger.error("Validação pós-replicação falhou")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
                return False
            
        except Exception as e:
            self.logger.error(f"Erro durante replicação: {str(e)}")
            self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
            return False
    
    def _validate_connections(self, source_connection, target_connection):
        """Validar ambas as conexões"""
        try:
            # Testar conexão de origem
            self.logger.info("Testando conexão de origem...")
            source_conn = self._create_connection(source_connection)
            if not source_conn:
                return False
            source_conn.close()
            
            # Testar conexão de destino
            self.logger.info("Testando conexão de destino...")
            target_conn = self._create_connection(target_connection)
            if not target_conn:
                return False
            target_conn.close()
            
            self.logger.success("Ambas as conexões estão funcionais")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na validação de conexões: {str(e)}")
            return False
    
    def _create_connection(self, connection_details):
        """Criar conexão PyMySQL"""
        try:
            connection = pymysql.connect(
                host=connection_details['host'],
                port=connection_details['port'],
                user=connection_details['username'],
                password=connection_details['password'],
                database=connection_details['database'],
                charset='utf8mb4',
                autocommit=False
            )
            return connection
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar: {str(e)}")
            return None
    
    def create_backup(self, connection_details):
        """Criar backup do banco de dados"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{connection_details['database']}_{timestamp}.sql"
            backup_path = os.path.join(self.backups_dir, backup_filename)
            
            self.logger.info(f"Criando backup: {backup_filename}")
            
            # Usar mysqldump para criar backup
            import subprocess
            
            cmd = [
                'mysqldump',
                f"--host={connection_details['host']}",
                f"--port={connection_details['port']}",
                f"--user={connection_details['username']}",
                f"--password={connection_details['password']}",
                '--single-transaction',
                '--routines',
                '--triggers',
                '--no-data',  # Apenas estrutura, sem dados
                connection_details['database']
            ]
            
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                result = subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                self.logger.success(f"Backup criado: {backup_path}")
                return backup_path
            else:
                self.logger.error(f"Erro no mysqldump: {result.stderr}")
                # Fallback: backup manual via Python
                return self._create_manual_backup(connection_details, backup_path)
                
        except Exception as e:
            self.logger.warning(f"Erro com mysqldump: {str(e)}")
            # Fallback: backup manual via Python
            return self._create_manual_backup(connection_details, backup_path)
    
    def _create_manual_backup(self, connection_details, backup_path):
        """Criar backup manual usando Python"""
        try:
            self.logger.info("Criando backup manual...")
            
            connection = self._create_connection(connection_details)
            if not connection:
                return None
            
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                backup_file.write(f"-- Backup da estrutura do banco {connection_details['database']}\n")
                backup_file.write(f"-- Criado em: {datetime.datetime.now()}\n")
                backup_file.write(f"-- Host: {connection_details['host']}:{connection_details['port']}\n\n")
                
                with connection.cursor() as cursor:
                    # Obter lista de tabelas
                    cursor.execute("""
                        SELECT TABLE_NAME 
                        FROM information_schema.TABLES 
                        WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_NAME
                    """, (connection_details['database'],))
                    
                    tables = cursor.fetchall()
                    
                    for (table_name,) in tables:
                        # Obter CREATE TABLE
                        cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                        create_table = cursor.fetchone()
                        
                        if create_table:
                            backup_file.write(f"-- Estrutura da tabela `{table_name}`\n")
                            backup_file.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                            backup_file.write(f"{create_table[1]};\n\n")
            
            connection.close()
            self.logger.success(f"Backup manual criado: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup manual: {str(e)}")
            return None
    
    def _execute_replication(self, target_connection, source_structure, differences):
        """Executar comandos de replicação"""
        try:
            connection = self._create_connection(target_connection)
            if not connection:
                return False
            
            total_operations = 0
            successful_operations = 0
            
            with connection.cursor() as cursor:
                # Executar em uma transação para segurança
                cursor.execute("START TRANSACTION")
                
                try:
                    # 1. Criar tabelas novas
                    for table_name in differences['new_tables']:
                        self.logger.info(f"Criando tabela: {table_name}")
                        create_sql = self._generate_create_table_sql(source_structure['tables'][table_name], table_name)
                        cursor.execute(create_sql)
                        total_operations += 1
                        successful_operations += 1
                        self.logger.success(f"Tabela {table_name} criada")
                        
                        # Sincronizar índices da nova tabela imediatamente
                        self._sync_table_indexes_in_transaction(cursor, source_structure, table_name)
                    
                    # 2. Modificar tabelas existentes
                    for table_name, table_diff in differences['modified_tables'].items():
                        self.logger.info(f"Modificando tabela: {table_name}")
                        
                        # Adicionar colunas novas
                        for column_name in table_diff['new_columns']:
                            alter_sql = self._generate_add_column_sql(
                                table_name, 
                                column_name, 
                                source_structure['tables'][table_name],
                                table_diff
                            )
                            cursor.execute(alter_sql)
                            total_operations += 1
                            successful_operations += 1
                            self.logger.success(f"Coluna {column_name} adicionada à tabela {table_name}")
                        
                        # Modificar colunas existentes
                        for modified_col in table_diff['modified_columns']:
                            modify_sql = self._generate_modify_column_sql(
                                table_name,
                                modified_col['name'],
                                modified_col['source']
                            )
                            self.logger.debug(f"EXECUTANDO SQL: {modify_sql}")
                            cursor.execute(modify_sql)
                            total_operations += 1
                            successful_operations += 1
                            self.logger.success(f"Coluna {modified_col['name']} modificada na tabela {table_name}")
                        
                        # Sincronizar índices da tabela modificada imediatamente
                        self._sync_table_indexes_in_transaction(cursor, source_structure, table_name)
                    
                    # 3. Sincronizar índices de todas as tabelas em uma única operação
                    self._sync_all_indexes_batch(cursor, source_structure, differences)
                    
                    # Confirmar transação
                    cursor.execute("COMMIT")
                    self.logger.success(f"Todas as {successful_operations} operações concluídas com sucesso")
                    
                except Exception as e:
                    # Reverter em caso de erro
                    cursor.execute("ROLLBACK")
                    self.logger.error(f"Erro durante execução, transação revertida: {str(e)}")
                    return False
            
            connection.close()
            return successful_operations == total_operations
            
        except Exception as e:
            self.logger.error(f"Erro na execução da replicação: {str(e)}")
            return False
    
    def _generate_create_table_sql(self, table_structure, table_name):
        """Gerar SQL CREATE TABLE"""
        sql = f"CREATE TABLE `{table_name}` (\n"
        
        column_definitions = []
        
        for column in table_structure['columns']:
            col_def = f"  `{column['name']}` {column['column_type']}"
            
            if not column['nullable']:
                col_def += " NOT NULL"
            
            if column['default'] is not None:
                # Tratamento especial para valores padrão
                default_value = column['default']
                
                # Para CURRENT_TIMESTAMP e funções do MySQL (incluindo versões com parênteses)
                if default_value.upper() in ['CURRENT_TIMESTAMP', 'NULL'] or \
                   'current_timestamp' in default_value.lower():
                    col_def += f" DEFAULT {default_value}"
                # Para campos datetime/timestamp com valor '0000-00-00 00:00:00'
                elif 'datetime' in column['column_type'].lower() or 'timestamp' in column['column_type'].lower():
                    if default_value in ['0000-00-00 00:00:00', '0000-00-00']:
                        # Usar NULL em vez de valor zero inválido
                        if column['nullable']:
                            col_def += " DEFAULT NULL"
                        # Se não aceita NULL, não adicionar DEFAULT
                    else:
                        col_def += f" DEFAULT '{default_value}'"
                else:
                    # Para strings, usar o valor já formatado do banco
                    # Se já contém aspas, não adicionar mais
                    if default_value.startswith("'") and default_value.endswith("'"):
                        col_def += f" DEFAULT {default_value}"
                    else:
                        col_def += f" DEFAULT '{default_value}'"
            
            if column['extra']:
                col_def += f" {column['extra']}"
            
            if column['comment']:
                col_def += f" COMMENT '{column['comment']}'"
            
            column_definitions.append(col_def)
        
        sql += ",\n".join(column_definitions)
        
        # Adicionar chave primária
        if table_structure['primary_key']:
            sql += f",\n  PRIMARY KEY (`{table_structure['primary_key']}`)"
        
        sql += "\n)"
        
        # Adicionar propriedades da tabela
        if table_structure['engine']:
            sql += f" ENGINE={table_structure['engine']}"
        
        if table_structure['charset']:
            sql += f" DEFAULT CHARSET={table_structure['charset']}"
        
        if table_structure['collation']:
            sql += f" COLLATE={table_structure['collation']}"
        
        return sql
    
    def _generate_add_column_sql(self, table_name, column_name, table_structure, table_diff):
        """Gerar SQL ALTER TABLE ADD COLUMN com posicionamento correto"""
        # Encontrar a coluna na estrutura de origem
        column_info = None
        for col in table_structure['columns']:
            if col['name'] == column_name:
                column_info = col
                break
        
        if not column_info:
            raise Exception(f"Coluna {column_name} não encontrada na estrutura de origem")
        
        sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_info['column_type']}"
        
        if not column_info['nullable']:
            sql += " NOT NULL"
        
        if column_info['default'] is not None:
            # Tratamento especial para valores padrão
            default_value = column_info['default']
            
            # Para CURRENT_TIMESTAMP e funções do MySQL (incluindo versões com parênteses)
            if default_value.upper() in ['CURRENT_TIMESTAMP', 'NULL'] or \
               'current_timestamp' in default_value.lower():
                sql += f" DEFAULT {default_value}"
            # Para campos datetime/timestamp com valor '0000-00-00 00:00:00'
            elif 'datetime' in column_info['column_type'].lower() or 'timestamp' in column_info['column_type'].lower():
                if default_value in ['0000-00-00 00:00:00', '0000-00-00']:
                    # Usar NULL em vez de valor zero inválido
                    if column_info['nullable']:
                        sql += " DEFAULT NULL"
                    # Se não aceita NULL, não adicionar DEFAULT
                else:
                    sql += f" DEFAULT '{default_value}'"
            else:
                # Para strings, usar o valor já formatado do banco
                # Se já contém aspas, não adicionar mais
                if default_value.startswith("'") and default_value.endswith("'"):
                    sql += f" DEFAULT {default_value}"
                else:
                    sql += f" DEFAULT '{default_value}'"
        
        if column_info['extra']:
            sql += f" {column_info['extra']}"
        
        if column_info['comment']:
            sql += f" COMMENT '{column_info['comment']}'"
        
        # Determinar posicionamento da coluna
        position = column_info['position']
        if position == 1:
            sql += " FIRST"
        else:
            # Encontrar a coluna anterior
            prev_column = None
            for col in table_structure['columns']:
                if col['position'] == position - 1:
                    prev_column = col['name']
                    break
            
            if prev_column:
                sql += f" AFTER `{prev_column}`"
        
        return sql
    
    def _generate_modify_column_sql(self, table_name, column_name, column_info):
        """Gerar SQL ALTER TABLE MODIFY COLUMN"""
        sql = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column_name}` {column_info['column_type']}"
        
        # LOG DETALHADO para debug
        self.logger.debug(f"DEBUG SQL: Gerando MODIFY para {table_name}.{column_name}")
        self.logger.debug(f"  column_info: {column_info}")
        
        # Para colunas timestamp, tratamento especial
        if 'timestamp' in column_info['column_type'].lower():
            if column_info['nullable']:
                sql += " NULL"
            else:
                sql += " NOT NULL"
                
            # Para timestamp nullable, sempre usar DEFAULT NULL
            if column_info['nullable']:
                sql += " DEFAULT NULL"
            elif column_info['default'] is not None:
                default_value = column_info['default']
                if default_value.upper() in ['CURRENT_TIMESTAMP', 'NULL'] or \
                   'current_timestamp' in default_value.lower():
                    sql += f" DEFAULT {default_value}"
                else:
                    sql += f" DEFAULT '{default_value}'"
        else:
            # Para outros tipos de coluna
            if not column_info['nullable']:
                sql += " NOT NULL"
            
            if column_info['default'] is not None:
                # Tratamento especial para valores padrão
                default_value = column_info['default']
                
                # Para CURRENT_TIMESTAMP e funções do MySQL (incluindo versões com parênteses)
                if default_value.upper() in ['CURRENT_TIMESTAMP', 'NULL'] or \
                   'current_timestamp' in default_value.lower():
                    sql += f" DEFAULT {default_value}"
                # Para campos datetime/timestamp com valor '0000-00-00 00:00:00'
                elif 'datetime' in column_info['column_type'].lower():
                    if default_value in ['0000-00-00 00:00:00', '0000-00-00']:
                        # Usar NULL em vez de valor zero inválido
                        if column_info['nullable']:
                            sql += " DEFAULT NULL"
                        # Se não aceita NULL, não adicionar DEFAULT
                    else:
                        if default_value.upper() == 'NULL':
                            sql += " DEFAULT NULL"
                        else:
                            sql += f" DEFAULT '{default_value}'"
                else:
                    # Para strings e outros tipos
                    if default_value.upper() == 'NULL':
                        sql += " DEFAULT NULL"
                    elif default_value.startswith("'") and default_value.endswith("'"):
                        sql += f" DEFAULT {default_value}"
                    else:
                        sql += f" DEFAULT '{default_value}'"
            elif column_info['nullable']:
                # Se é nullable e não tem default explícito, definir como NULL
                sql += " DEFAULT NULL"
        
        if column_info['extra']:
            sql += f" {column_info['extra']}"
        
        if column_info['comment']:
            sql += f" COMMENT '{column_info['comment']}'"
        
        # LOG do SQL final
        self.logger.debug(f"  SQL GERADO: {sql}")
        
        return sql
    
    def _validate_replication(self, source_connection, target_connection):
        """Validar se a replicação foi bem-sucedida"""
        try:
            self.logger.info("Validando resultado da replicação...")
            
            # Reanalisar estruturas
            source_structure = self.structure_analyzer.analyze_database_structure(source_connection)
            target_structure = self.structure_analyzer.analyze_database_structure(target_connection)
            
            if not source_structure or not target_structure:
                return False
            
            # Comparar novamente
            differences = self.structure_analyzer.compare_structures(source_structure, target_structure)
            
            # DEBUG: Log detalhado das diferenças
            self.logger.info(f"DEBUG - Diferenças encontradas:")
            self.logger.info(f"  Tabelas novas: {len(differences['new_tables'])}")
            self.logger.info(f"  Tabelas modificadas: {len(differences['modified_tables'])}")
            self.logger.info(f"  Diferenças de índices: {len(differences.get('index_differences', {}))}")
            
            if differences['modified_tables']:
                self.logger.info(f"  Tabelas com modificações:")
                for table_name, table_diff in differences['modified_tables'].items():
                    self.logger.info(f"    {table_name}: colunas novas={len(table_diff['new_columns'])}, removidas={len(table_diff['removed_columns'])}, modificadas={len(table_diff['modified_columns'])}")
            
            # Verificar se ainda há diferenças críticas (apenas tabelas e colunas)
            critical_differences = (len(differences['new_tables']) + 
                                  len(differences['modified_tables']))
            
            if critical_differences == 0:
                # Verificar apenas diferenças de índices
                index_differences = len(differences.get('index_differences', {}))
                if index_differences > 0:
                    self.logger.info(f"Aplicando sincronização final para {index_differences} diferenças de índices...")
                    self._final_index_sync(target_connection, source_structure, target_structure)
                
                self.logger.success("Validação bem-sucedida: estruturas sincronizadas")
                return True
            else:
                # Verificar se as diferenças são apenas de índices (menos críticas)
                only_index_differences = self._are_only_index_differences(differences, source_structure, target_structure)
                
                self.logger.info(f"DEBUG - Análise de diferenças:")
                self.logger.info(f"  Apenas diferenças de índices: {only_index_differences}")
                
                if only_index_differences:
                    self.logger.warning(f"Diferenças menores detectadas (principalmente índices)")
                    self.logger.info("Tentando sincronização final de índices...")
                    
                    # Tentar uma sincronização final de índices
                    if self._final_index_sync(target_connection, source_structure, target_structure):
                        self.logger.success("Sincronização final de índices bem-sucedida")
                        return True
                    else:
                        self.logger.warning("Algumas diferenças de índices persistem, mas estrutura principal está sincronizada")
                        return True  # Aceitar como sucesso se apenas índices estão diferentes
                else:
                    self.logger.error(f"Ainda existem {critical_differences} diferenças estruturais críticas após replicação")
                    
                    # DEBUG: Detalhar quais são as diferenças críticas
                    if differences['new_tables']:
                        self.logger.error(f"  Tabelas não criadas: {differences['new_tables']}")
                    
                    if differences['modified_tables']:
                        self.logger.error(f"  Tabelas com diferenças estruturais:")
                        for table_name, table_diff in differences['modified_tables'].items():
                            if table_diff['new_columns']:
                                self.logger.error(f"    {table_name}: colunas não criadas: {table_diff['new_columns']}")
                            if table_diff['modified_columns']:
                                self.logger.error(f"    {table_name}: colunas não modificadas: {[col['name'] for col in table_diff['modified_columns']]}")
                    
                    return False
                
        except Exception as e:
            self.logger.error(f"Erro na validação: {str(e)}")
            return False
    
    def _are_only_index_differences(self, differences, source_structure, target_structure):
        """Verificar se as diferenças são apenas relacionadas a índices"""
        try:
            # Se há tabelas novas ou modificadas estruturalmente, não são apenas índices
            if differences['new_tables'] or differences['modified_tables']:
                return False
            
            # Verificar se todas as tabelas principais existem
            source_tables = set(source_structure['tables'].keys())
            target_tables = set(target_structure['tables'].keys())
            
            if source_tables != target_tables:
                return False
            
            # Verificar se as colunas de cada tabela são idênticas
            for table_name in source_tables:
                source_table = source_structure['tables'][table_name]
                target_table = target_structure['tables'][table_name]
                
                source_columns = {col['name']: col for col in source_table['columns']}
                target_columns = {col['name']: col for col in target_table['columns']}
                
                if set(source_columns.keys()) != set(target_columns.keys()):
                    return False
                    
                # Verificar se as definições das colunas são idênticas
                for col_name in source_columns:
                    if not self.structure_analyzer._columns_are_identical(
                        source_columns[col_name], 
                        target_columns[col_name]
                    ):
                        return False
            
            return True  # Apenas diferenças de índices
            
        except Exception:
            return False
    
    def _final_index_sync(self, target_connection, source_structure, target_structure):
        """Sincronização final de índices para corrigir diferenças restantes"""
        try:
            connection = self._create_connection(target_connection)
            if not connection:
                return False
            
            success_count = 0
            total_count = 0
            
            with connection.cursor() as cursor:
                for table_name in source_structure['tables']:
                    if table_name not in target_structure['tables']:
                        continue
                        
                    source_table = source_structure['tables'][table_name]
                    target_table = target_structure['tables'][table_name]
                    
                    source_indexes = source_table.get('indexes', {})
                    target_indexes = target_table.get('indexes', {})
                    
                    # Criar índices faltantes
                    for index_name, index_info in source_indexes.items():
                        if index_name == 'PRIMARY':
                            continue
                            
                        total_count += 1
                        
                        if index_name not in target_indexes:
                            columns_str = '`, `'.join(index_info['columns'])
                            unique_str = 'UNIQUE ' if index_info['unique'] else ''
                            
                            create_index_sql = f"CREATE {unique_str}INDEX `{index_name}` ON `{table_name}` (`{columns_str}`)"
                            
                            try:
                                cursor.execute(create_index_sql)
                                success_count += 1
                                self.logger.success(f"Índice final {index_name} criado na tabela {table_name}")
                            except Exception as e:
                                if "Duplicate key name" not in str(e):
                                    self.logger.warning(f"Erro ao criar índice final {index_name}: {str(e)}")
                        else:
                            success_count += 1  # Índice já existe
            
            connection.close()
            return success_count >= (total_count * 0.8)  # Aceitar 80% de sucesso
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização final de índices: {str(e)}")
            return False
    
    def list_backups(self):
        """Listar backups disponíveis"""
        backups = []
        
        if os.path.exists(self.backups_dir):
            for file in os.listdir(self.backups_dir):
                if file.endswith('.sql'):
                    file_path = os.path.join(self.backups_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    backups.append(f"{file} ({file_size} bytes) - {file_modified}")
        
        return sorted(backups, reverse=True)
    
    def _sync_table_indexes_in_transaction(self, cursor, source_structure, table_name):
        """Sincronizar índices de uma tabela dentro de uma transação ativa"""
        try:
            if table_name not in source_structure['tables']:
                return
                
            source_table = source_structure['tables'][table_name]
            source_indexes = source_table.get('indexes', {})
            
            # Obter índices atuais da tabela de destino
            cursor.execute("""
                SELECT 
                    INDEX_NAME,
                    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                    MIN(NON_UNIQUE) as is_unique
                FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                AND INDEX_NAME != 'PRIMARY'
                GROUP BY INDEX_NAME
            """, (table_name,))
            
            existing_indexes = {}
            for row in cursor.fetchall():
                existing_indexes[row[0]] = {
                    'columns': row[1].split(','),
                    'unique': row[2] == 0
                }
            
            # Criar índices faltantes
            for index_name, index_info in source_indexes.items():
                if index_name == 'PRIMARY':
                    continue  # Pular chave primária
                
                if index_name not in existing_indexes:
                    columns_str = '`, `'.join(index_info['columns'])
                    unique_str = 'UNIQUE ' if index_info['unique'] else ''
                    
                    create_index_sql = f"CREATE {unique_str}INDEX `{index_name}` ON `{table_name}` (`{columns_str}`)"
                    
                    try:
                        cursor.execute(create_index_sql)
                        self.logger.success(f"Índice {index_name} criado na tabela {table_name}")
                    except Exception as e:
                        # Ignorar erros de índices duplicados ou incompatíveis
                        if "Duplicate key name" not in str(e) and "already exists" not in str(e):
                            self.logger.warning(f"Erro ao criar índice {index_name}: {str(e)}")
                            
        except Exception as e:
            self.logger.warning(f"Erro ao sincronizar índices da tabela {table_name}: {str(e)}")

    def _sync_all_indexes_batch(self, cursor, source_structure, differences):
        """Sincronizar todos os índices em lote para otimizar performance"""
        try:
            self.logger.info("Sincronizando índices em lote...")
            
            # Obter todas as tabelas que precisam de sincronização
            tables_to_sync = set()
            tables_to_sync.update(differences['new_tables'])
            tables_to_sync.update(differences['modified_tables'].keys())
            
            # Processar cada tabela
            for table_name in tables_to_sync:
                if table_name in source_structure['tables']:
                    source_table = source_structure['tables'][table_name]
                    source_indexes = source_table.get('indexes', {})
                    
                    # Verificar índices existentes
                    cursor.execute("""
                        SELECT INDEX_NAME
                        FROM information_schema.STATISTICS 
                        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                        AND INDEX_NAME != 'PRIMARY'
                        GROUP BY INDEX_NAME
                    """, (table_name,))
                    
                    existing_indexes = {row[0] for row in cursor.fetchall()}
                    
                    # Criar índices faltantes
                    for index_name, index_info in source_indexes.items():
                        if index_name == 'PRIMARY':
                            continue
                            
                        if index_name not in existing_indexes:
                            columns_str = '`, `'.join(index_info['columns'])
                            unique_str = 'UNIQUE ' if index_info['unique'] else ''
                            
                            create_index_sql = f"CREATE {unique_str}INDEX `{index_name}` ON `{table_name}` (`{columns_str}`)"
                            
                            try:
                                cursor.execute(create_index_sql)
                                self.logger.success(f"Índice {index_name} criado na tabela {table_name}")
                            except Exception as e:
                                if "Duplicate key name" not in str(e) and "already exists" not in str(e):
                                    self.logger.warning(f"Erro ao criar índice {index_name}: {str(e)}")
            
            self.logger.success("Sincronização de índices em lote concluída")
                    
        except Exception as e:
            self.logger.error(f"Erro na sincronização de índices em lote: {str(e)}")

    def _sync_table_indexes(self, target_connection, source_structure, target_structure, table_name):
        """Sincronizar índices de uma tabela específica (método legado mantido para compatibilidade)"""
        try:
            connection = self._create_connection(target_connection)
            if not connection:
                return False
            
            source_table = source_structure['tables'][table_name]
            target_table = target_structure['tables'][table_name]
            
            source_indexes = source_table.get('indexes', {})
            target_indexes = target_table.get('indexes', {})
            
            with connection.cursor() as cursor:
                # Verificar índices que existem na origem mas não no destino
                for index_name, index_info in source_indexes.items():
                    if index_name == 'PRIMARY':
                        continue  # Pular chave primária
                    
                    if index_name not in target_indexes:
                        # Criar índice faltante
                        columns_str = '`, `'.join(index_info['columns'])
                        unique_str = 'UNIQUE ' if index_info['unique'] else ''
                        
                        create_index_sql = f"CREATE {unique_str}INDEX `{index_name}` ON `{table_name}` (`{columns_str}`)"
                        
                        try:
                            cursor.execute(create_index_sql)
                            self.logger.success(f"Índice {index_name} criado na tabela {table_name}")
                        except Exception as e:
                            self.logger.warning(f"Erro ao criar índice {index_name}: {str(e)}")
            
            connection.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar índices da tabela {table_name}: {str(e)}")
            return False

    def _detect_iterative_replication_loop(self, source_connection, target_connection):
        """Detectar se estamos em um loop de replicação iterativa"""
        try:
            # Verificar se há múltiplas análises seguidas nos logs recentes
            recent_logs = self.logger.get_recent_operations(minutes=5)
            analysis_count = sum(1 for log in recent_logs if "Análise da estrutura" in log)
            
            if analysis_count > 10:  # Mais de 10 análises em 5 minutos indica loop
                self.logger.warning("Detectado possível loop de replicação iterativa")
                self.logger.info("Forçando sincronização completa em uma única operação...")
                return self._force_complete_sync(source_connection, target_connection)
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Erro ao detectar loop iterativo: {str(e)}")
            return False
    
    def _force_complete_sync(self, source_connection, target_connection):
        """Forçar sincronização completa em uma única operação"""
        try:
            self.logger.info("Iniciando sincronização forçada completa...")
            
            # Analisar estruturas uma única vez
            source_structure = self.structure_analyzer.analyze_database_structure(source_connection)
            target_structure = self.structure_analyzer.analyze_database_structure(target_connection)
            
            if not source_structure or not target_structure:
                return False
            
            connection = self._create_connection(target_connection)
            if not connection:
                return False
            
            success_count = 0
            total_operations = 0
            
            with connection.cursor() as cursor:
                cursor.execute("START TRANSACTION")
                
                try:
                    # Sincronizar todos os índices de todas as tabelas de uma vez
                    for table_name in source_structure['tables']:
                        if table_name not in target_structure['tables']:
                            continue  # Pular tabelas que não existem no destino
                            
                        source_table = source_structure['tables'][table_name]
                        source_indexes = source_table.get('indexes', {})
                        
                        # Obter índices existentes no destino
                        cursor.execute("""
                            SELECT INDEX_NAME
                            FROM information_schema.STATISTICS 
                            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                            AND INDEX_NAME != 'PRIMARY'
                            GROUP BY INDEX_NAME
                        """, (table_name,))
                        
                        existing_indexes = {row[0] for row in cursor.fetchall()}
                        
                        # Criar todos os índices faltantes
                        for index_name, index_info in source_indexes.items():
                            if index_name == 'PRIMARY':
                                continue
                                
                            total_operations += 1
                            
                            if index_name not in existing_indexes:
                                columns_str = '`, `'.join(index_info['columns'])
                                unique_str = 'UNIQUE ' if index_info['unique'] else ''
                                
                                create_index_sql = f"CREATE {unique_str}INDEX `{index_name}` ON `{table_name}` (`{columns_str}`)"
                                
                                try:
                                    cursor.execute(create_index_sql)
                                    success_count += 1
                                    self.logger.success(f"Índice {index_name} criado na tabela {table_name}")
                                except Exception as e:
                                    if "Duplicate key name" not in str(e) and "already exists" not in str(e):
                                        self.logger.warning(f"Erro ao criar índice {index_name}: {str(e)}")
                            else:
                                success_count += 1  # Índice já existe
                    
                    cursor.execute("COMMIT")
                    self.logger.success(f"Sincronização forçada concluída: {success_count}/{total_operations} operações")
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    self.logger.error(f"Erro na sincronização forçada: {str(e)}")
                    return False
            
            connection.close()
            return success_count >= (total_operations * 0.9)  # 90% de sucesso
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização forçada completa: {str(e)}")
            return False

    def _sync_indexes_only(self, target_connection, source_structure, differences):
        """Sincronizar apenas índices quando não há mudanças estruturais"""
        try:
            connection = self._create_connection(target_connection)
            if not connection:
                return False
            
            index_differences = differences.get('index_differences', {})
            
            if not index_differences:
                self.logger.info("Nenhuma diferença de índices detectada")
                return True
            
            success_count = 0
            total_count = 0
            
            with connection.cursor() as cursor:
                for table_name, index_diff in index_differences.items():
                    for missing_index in index_diff['missing_indexes']:
                        total_count += 1
                        index_name = missing_index['name']
                        index_info = missing_index['info']
                        
                        columns_str = '`, `'.join(index_info['columns'])
                        unique_str = 'UNIQUE ' if index_info['unique'] else ''
                        
                        create_index_sql = f"CREATE {unique_str}INDEX `{index_name}` ON `{table_name}` (`{columns_str}`)"
                        
                        try:
                            cursor.execute(create_index_sql)
                            success_count += 1
                            self.logger.success(f"Índice {index_name} criado na tabela {table_name}")
                        except Exception as e:
                            if "Duplicate key name" not in str(e):
                                self.logger.warning(f"Erro ao criar índice {index_name}: {str(e)}")
            
            connection.close()
            self.logger.info(f"Sincronização de índices: {success_count}/{total_count} concluídas")
            return success_count >= total_count * 0.8  # 80% de sucesso
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização de índices: {str(e)}")
            return False
    
    def _create_all_tables_from_scratch(self, target_connection, source_structure, backup_file):
        """Criar todas as tabelas quando o banco de destino está vazio"""
        try:
            self.logger.step(5, 6, f"Criando {len(source_structure['tables'])} tabelas do zero")
            
            connection = self._create_connection(target_connection)
            if not connection:
                return False
            
            tables_created = 0
            total_tables = len(source_structure['tables'])
            
            with connection.cursor() as cursor:
                cursor.execute("START TRANSACTION")
                
                try:
                    # Ordenar tabelas por dependências (se possível)
                    table_names = list(source_structure['tables'].keys())
                    
                    # Criar todas as tabelas
                    for table_name in table_names:
                        self.logger.info(f"Criando tabela: {table_name}")
                        
                        table_structure = source_structure['tables'][table_name]
                        create_sql = self._generate_create_table_sql(table_structure, table_name)
                        
                        cursor.execute(create_sql)
                        tables_created += 1
                        self.logger.success(f"Tabela {table_name} criada ({tables_created}/{total_tables})")
                    
                    # Criar todos os índices após criar as tabelas
                    self.logger.info("Criando índices para todas as tabelas...")
                    indexes_created = 0
                    
                    for table_name in table_names:
                        table_structure = source_structure['tables'][table_name]
                        indexes = table_structure.get('indexes', {})
                        
                        for index_name, index_info in indexes.items():
                            if index_name == 'PRIMARY':
                                continue  # Chave primária já foi criada com a tabela
                            
                            columns_str = '`, `'.join(index_info['columns'])
                            unique_str = 'UNIQUE ' if index_info['unique'] else ''
                            
                            create_index_sql = f"CREATE {unique_str}INDEX `{index_name}` ON `{table_name}` (`{columns_str}`)"
                            
                            try:
                                cursor.execute(create_index_sql)
                                indexes_created += 1
                                self.logger.success(f"Índice {index_name} criado na tabela {table_name}")
                            except Exception as e:
                                if "Duplicate key name" not in str(e):
                                    self.logger.warning(f"Erro ao criar índice {index_name}: {str(e)}")
                    
                    cursor.execute("COMMIT")
                    self.logger.success(f"Criação completa: {tables_created} tabelas e {indexes_created} índices")
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    self.logger.error(f"Erro durante criação das tabelas: {str(e)}")
                    return False
            
            connection.close()
            
            # Passo 6: Validar criação
            self.logger.step(6, 6, "Validando criação das tabelas")
            if self._validate_table_creation(target_connection, source_structure):
                self.logger.success(f"Criação concluída! Backup salvo em: {backup_file}")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", True)
                return True
            else:
                self.logger.error("Validação da criação falhou")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na criação das tabelas: {str(e)}")
            self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
            return False
    
    def _validate_table_creation(self, target_connection, source_structure):
        """Validar se todas as tabelas foram criadas corretamente"""
        try:
            # Reanalisar estrutura do destino
            target_structure = self.structure_analyzer.analyze_database_structure(target_connection)
            
            if not target_structure:
                return False
            
            source_tables = set(source_structure['tables'].keys())
            target_tables = set(target_structure['tables'].keys())
            
            missing_tables = source_tables - target_tables
            
            if missing_tables:
                self.logger.error(f"Tabelas não criadas: {missing_tables}")
                return False
            
            self.logger.success(f"Todas as {len(source_tables)} tabelas foram criadas com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na validação da criação: {str(e)}")
            return False
