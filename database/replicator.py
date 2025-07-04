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
            
            # Verificar se há alterações
            total_changes = (len(differences['new_tables']) + 
                           len(differences['modified_tables']))
            
            if total_changes == 0:
                self.logger.success("Estruturas já estão sincronizadas!")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", True)
                return True
            
            # Passo 5: Gerar e executar comandos SQL
            self.logger.step(5, 6, f"Executando {total_changes} alterações")
            success = self._execute_replication(target_connection, source_structure, differences)
            
            if not success:
                self.logger.error("Falha durante a replicação")
                self.logger.operation_end("REPLICAÇÃO DE ESTRUTURA", False)
                return False
            
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
                            cursor.execute(modify_sql)
                            total_operations += 1
                            successful_operations += 1
                            self.logger.success(f"Coluna {modified_col['name']} modificada na tabela {table_name}")
                    
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
            
            # Verificar se ainda há diferenças críticas
            critical_differences = (len(differences['new_tables']) + 
                                  len(differences['modified_tables']))
            
            if critical_differences == 0:
                self.logger.success("Validação bem-sucedida: estruturas sincronizadas")
                return True
            else:
                self.logger.warning(f"Ainda existem {critical_differences} diferenças após replicação")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na validação: {str(e)}")
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
