#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizador de dados entre ambientes
"""

import pymysql
from config.data_sync_config import DataSyncConfig

class DataSynchronizer:
    def __init__(self, logger):
        """Inicializar sincronizador de dados"""
        self.logger = logger
        self.config = DataSyncConfig(logger)
    
    def sync_all_configured_tables(self, source_connection, target_connection, direction='to_prod'):
        """Sincronizar todas as tabelas configuradas"""
        try:
            self.logger.operation_start(f"SINCRONIZAÇÃO DE DADOS - {direction.upper()}")
            
            # Obter tabelas ativas para sincronização
            sync_tables = self.config.get_active_sync_tables()
            
            if not sync_tables:
                self.logger.warning("Nenhuma tabela configurada para sincronização")
                self.logger.operation_end("SINCRONIZAÇÃO DE DADOS", True)
                return True
            
            total_tables = len(sync_tables)
            success_count = 0
            
            self.logger.info(f"Sincronizando {total_tables} tabelas configuradas...")
            
            for i, table_config in enumerate(sync_tables, 1):
                table_name = table_config['table_name']
                
                self.logger.step(i, total_tables, f"Sincronizando tabela: {table_name}")
                
                # Iniciar registro de histórico
                history_id = self.config.add_sync_history(
                    table_name, direction, source_connection, target_connection
                )
                
                try:
                    records_affected = self._sync_table_data(
                        table_config, source_connection, target_connection, direction
                    )
                    
                    if records_affected is not None:
                        success_count += 1
                        self.logger.success(f"Tabela {table_name}: {records_affected} registros processados")
                        
                        # Atualizar histórico com sucesso
                        if history_id:
                            self.config.update_sync_history(history_id, records_affected, 'success')
                    else:
                        self.logger.error(f"Falha na sincronização da tabela {table_name}")
                        
                        # Atualizar histórico com erro
                        if history_id:
                            self.config.update_sync_history(history_id, 0, 'error', 'Erro na sincronização')
                
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar tabela {table_name}: {str(e)}")
                    
                    # Atualizar histórico com erro
                    if history_id:
                        self.config.update_sync_history(history_id, 0, 'error', str(e))
            
            # Resultado final
            if success_count == total_tables:
                self.logger.success(f"Todas as {total_tables} tabelas sincronizadas com sucesso!")
                self.logger.operation_end("SINCRONIZAÇÃO DE DADOS", True)
                return True
            else:
                self.logger.warning(f"Sincronização parcial: {success_count}/{total_tables} tabelas")
                self.logger.operation_end("SINCRONIZAÇÃO DE DADOS", False)
                return False
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização de dados: {str(e)}")
            self.logger.operation_end("SINCRONIZAÇÃO DE DADOS", False)
            return False
    
    def _sync_table_data(self, table_config, source_connection, target_connection, direction):
        """Sincronizar dados de uma tabela específica"""
        try:
            table_name = table_config['table_name']
            sync_type = table_config['sync_type']
            primary_key = table_config['primary_key']
            
            # Criar conexões
            source_conn = self._create_connection(source_connection)
            target_conn = self._create_connection(target_connection)
            
            if not source_conn or not target_conn:
                return None
            
            records_affected = 0
            
            if sync_type == 'full':
                records_affected = self._sync_full_table(
                    table_name, primary_key, source_conn, target_conn
                )
            elif sync_type == 'incremental':
                records_affected = self._sync_incremental_table(
                    table_name, primary_key, source_conn, target_conn
                )
            elif sync_type == 'key_only':
                records_affected = self._sync_key_only_table(
                    table_name, primary_key, source_conn, target_conn
                )
            
            # Fechar conexões
            source_conn.close()
            target_conn.close()
            
            return records_affected
            
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar dados da tabela {table_name}: {str(e)}")
            return None
    
    def _sync_full_table(self, table_name, primary_key, source_conn, target_conn):
        """Sincronização completa da tabela (substitui todos os dados)"""
        try:
            with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:
                # Obter estrutura da tabela
                source_cursor.execute(f"DESCRIBE `{table_name}`")
                columns_info = source_cursor.fetchall()
                column_names = [col[0] for col in columns_info]
                columns_str = '`, `'.join(column_names)
                
                # Verificar se a tabela existe no destino
                target_cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = DATABASE() AND table_name = %s
                """, (table_name,))
                
                if target_cursor.fetchone()[0] == 0:
                    self.logger.warning(f"Tabela '{table_name}' não existe no destino - pulando sincronização")
                    return 0
                
                # Obter todos os dados da origem
                source_cursor.execute(f"SELECT `{columns_str}` FROM `{table_name}`")
                source_data = source_cursor.fetchall()
                
                if not source_data:
                    self.logger.info(f"Tabela '{table_name}' está vazia na origem")
                    return 0
                
                # Iniciar transação no destino
                target_conn.begin()
                
                try:
                    # Limpar tabela de destino (exceto se for tabela crítica)
                    if not self._is_critical_table(table_name):
                        target_cursor.execute(f"DELETE FROM `{table_name}`")
                        self.logger.info(f"Tabela '{table_name}' limpa no destino")
                    
                    # Inserir dados da origem
                    placeholders = ', '.join(['%s'] * len(column_names))
                    insert_sql = f"INSERT INTO `{table_name}` (`{columns_str}`) VALUES ({placeholders})"
                    
                    # Inserir em lotes para performance
                    batch_size = 1000
                    total_inserted = 0
                    
                    for i in range(0, len(source_data), batch_size):
                        batch = source_data[i:i + batch_size]
                        target_cursor.executemany(insert_sql, batch)
                        total_inserted += len(batch)
                        
                        if total_inserted % 5000 == 0:
                            self.logger.info(f"Inseridos {total_inserted} registros em '{table_name}'...")
                    
                    target_conn.commit()
                    self.logger.success(f"Sincronização completa: {total_inserted} registros inseridos em '{table_name}'")
                    return total_inserted
                
                except Exception as e:
                    target_conn.rollback()
                    raise e
                
        except Exception as e:
            self.logger.error(f"Erro na sincronização completa da tabela '{table_name}': {str(e)}")
            return None
    
    def _sync_incremental_table(self, table_name, primary_key, source_conn, target_conn):
        """Sincronização incremental (apenas registros novos/modificados)"""
        try:
            with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:
                # Obter estrutura da tabela
                source_cursor.execute(f"DESCRIBE `{table_name}`")
                columns_info = source_cursor.fetchall()
                column_names = [col[0] for col in columns_info]
                columns_str = '`, `'.join(column_names)
                
                # Verificar se a tabela tem coluna de timestamp para comparação
                has_updated_at = any(col for col in column_names if col in ['updated_at', 'modified_at', 'timestamp'])
                
                if has_updated_at:
                    return self._sync_by_timestamp(table_name, column_names, source_conn, target_conn)
                else:
                    return self._sync_by_comparison(table_name, primary_key, column_names, source_conn, target_conn)
                
        except Exception as e:
            self.logger.error(f"Erro na sincronização incremental da tabela '{table_name}': {str(e)}")
            return None
    
    def _sync_key_only_table(self, table_name, primary_key, source_conn, target_conn):
        """Sincronização apenas de chaves (para tabelas de referência)"""
        try:
            with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:
                # Obter apenas as chaves primárias da origem
                source_cursor.execute(f"SELECT DISTINCT `{primary_key}` FROM `{table_name}`")
                source_keys = {row[0] for row in source_cursor.fetchall()}
                
                if not source_keys:
                    return 0
                
                # Obter chaves existentes no destino
                target_cursor.execute(f"SELECT DISTINCT `{primary_key}` FROM `{table_name}`")
                target_keys = {row[0] for row in target_cursor.fetchall()}
                
                # Encontrar chaves que existem na origem mas não no destino
                missing_keys = source_keys - target_keys
                
                if not missing_keys:
                    self.logger.info(f"Tabela '{table_name}': todas as chaves já existem no destino")
                    return 0
                
                # Obter registros completos das chaves faltantes
                keys_list = list(missing_keys)
                placeholders = ', '.join(['%s'] * len(keys_list))
                
                source_cursor.execute(f"""
                    SELECT * FROM `{table_name}` 
                    WHERE `{primary_key}` IN ({placeholders})
                """, keys_list)
                
                missing_records = source_cursor.fetchall()
                
                if missing_records:
                    # Obter nomes das colunas
                    source_cursor.execute(f"DESCRIBE `{table_name}`")
                    columns_info = source_cursor.fetchall()
                    column_names = [col[0] for col in columns_info]
                    columns_str = '`, `'.join(column_names)
                    
                    # Inserir registros faltantes
                    placeholders = ', '.join(['%s'] * len(column_names))
                    insert_sql = f"INSERT INTO `{table_name}` (`{columns_str}`) VALUES ({placeholders})"
                    
                    target_cursor.executemany(insert_sql, missing_records)
                    target_conn.commit()
                    
                    self.logger.success(f"Inseridos {len(missing_records)} novos registros em '{table_name}'")
                    return len(missing_records)
                
                return 0
                
        except Exception as e:
            self.logger.error(f"Erro na sincronização por chaves da tabela '{table_name}': {str(e)}")
            return None
    
    def _sync_by_timestamp(self, table_name, column_names, source_conn, target_conn):
        """Sincronização baseada em timestamp de modificação"""
        # Implementação para sincronização por timestamp
        # Por enquanto, usar sincronização por comparação
        return self._sync_by_comparison(table_name, 'id', column_names, source_conn, target_conn)
    
    def _sync_by_comparison(self, table_name, primary_key, column_names, source_conn, target_conn):
        """Sincronização baseada em comparação de registros"""
        try:
            with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:
                # Obter todos os registros da origem
                columns_str = '`, `'.join(column_names)
                source_cursor.execute(f"SELECT `{columns_str}` FROM `{table_name}`")
                source_records = {row[0]: row for row in source_cursor.fetchall()}  # Assumindo que a primeira coluna é a PK
                
                # Obter todos os registros do destino
                target_cursor.execute(f"SELECT `{columns_str}` FROM `{table_name}`")
                target_records = {row[0]: row for row in target_cursor.fetchall()}
                
                # Encontrar registros para inserir/atualizar
                records_to_process = []
                
                for pk, source_record in source_records.items():
                    if pk not in target_records:
                        # Registro novo - inserir
                        records_to_process.append(('INSERT', source_record))
                    elif source_record != target_records[pk]:
                        # Registro modificado - atualizar
                        records_to_process.append(('UPDATE', source_record))
                
                if not records_to_process:
                    return 0
                
                # Processar inserções e atualizações
                insertions = 0
                updates = 0
                
                for operation, record in records_to_process:
                    if operation == 'INSERT':
                        placeholders = ', '.join(['%s'] * len(column_names))
                        insert_sql = f"INSERT INTO `{table_name}` (`{columns_str}`) VALUES ({placeholders})"
                        target_cursor.execute(insert_sql, record)
                        insertions += 1
                    elif operation == 'UPDATE':
                        set_clause = ', '.join([f"`{col}` = %s" for col in column_names[1:]])  # Excluir PK
                        update_sql = f"UPDATE `{table_name}` SET {set_clause} WHERE `{primary_key}` = %s"
                        target_cursor.execute(update_sql, record[1:] + (record[0],))  # Valores + PK
                        updates += 1
                
                target_conn.commit()
                
                total_affected = insertions + updates
                self.logger.success(f"Tabela '{table_name}': {insertions} inserções, {updates} atualizações")
                return total_affected
                
        except Exception as e:
            self.logger.error(f"Erro na sincronização por comparação: {str(e)}")
            return None
    
    def _is_critical_table(self, table_name):
        """Verificar se uma tabela é crítica (não deve ser limpa completamente)"""
        critical_tables = {
            'users', 'user_passwords', 'permissions', 'roles', 
            'processes', 'log_actions', 'log_requests'
        }
        return table_name.lower() in critical_tables
    
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
    
    def sync_single_table(self, table_name, source_connection, target_connection, direction='to_prod'):
        """Sincronizar uma única tabela"""
        try:
            self.logger.operation_start(f"SINCRONIZAÇÃO DA TABELA: {table_name}")
            
            # Verificar se a tabela está configurada
            sync_tables = self.config.get_active_sync_tables()
            table_config = next((t for t in sync_tables if t['table_name'] == table_name), None)
            
            if not table_config:
                self.logger.error(f"Tabela '{table_name}' não está configurada para sincronização")
                self.logger.operation_end(f"SINCRONIZAÇÃO DA TABELA: {table_name}", False)
                return False
            
            # Iniciar registro de histórico
            history_id = self.config.add_sync_history(
                table_name, direction, source_connection, target_connection
            )
            
            try:
                records_affected = self._sync_table_data(
                    table_config, source_connection, target_connection, direction
                )
                
                if records_affected is not None:
                    self.logger.success(f"Sincronização concluída: {records_affected} registros processados")
                    
                    # Atualizar histórico com sucesso
                    if history_id:
                        self.config.update_sync_history(history_id, records_affected, 'success')
                    
                    self.logger.operation_end(f"SINCRONIZAÇÃO DA TABELA: {table_name}", True)
                    return True
                else:
                    self.logger.error(f"Falha na sincronização da tabela {table_name}")
                    
                    # Atualizar histórico com erro
                    if history_id:
                        self.config.update_sync_history(history_id, 0, 'error', 'Erro na sincronização')
                    
                    self.logger.operation_end(f"SINCRONIZAÇÃO DA TABELA: {table_name}", False)
                    return False
            
            except Exception as e:
                self.logger.error(f"Erro ao sincronizar tabela {table_name}: {str(e)}")
                
                # Atualizar histórico com erro
                if history_id:
                    self.config.update_sync_history(history_id, 0, 'error', str(e))
                
                self.logger.operation_end(f"SINCRONIZAÇÃO DA TABELA: {table_name}", False)
                return False
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização da tabela: {str(e)}")
            self.logger.operation_end(f"SINCRONIZAÇÃO DA TABELA: {table_name}", False)
            return False
