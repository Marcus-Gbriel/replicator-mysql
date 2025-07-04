#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações de sincronização de dados entre ambientes
"""

import os
import json
import sqlite3
from datetime import datetime

class DataSyncConfig:
    def __init__(self, logger):
        """Inicializar configurador de sincronização de dados"""
        self.logger = logger
        self.config_db_path = os.path.join("config", "replicator.db")
        self._init_data_sync_tables()
    
    def _init_data_sync_tables(self):
        """Inicializar tabelas de configuração de sincronização de dados"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            # Tabela para configurações de sincronização de dados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sync_tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    sync_type TEXT DEFAULT 'full',  -- 'full', 'incremental', 'key_only'
                    primary_key_column TEXT DEFAULT 'id',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active INTEGER DEFAULT 1
                )
            """)
            
            # Tabela para configurações específicas de colunas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sync_columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    sync_enabled INTEGER DEFAULT 1,
                    sync_direction TEXT DEFAULT 'both',  -- 'both', 'to_prod', 'to_dev'
                    is_key_column INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (table_name) REFERENCES data_sync_tables(table_name)
                )
            """)
            
            # Tabela para histórico de sincronizações
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    sync_direction TEXT NOT NULL,
                    records_affected INTEGER DEFAULT 0,
                    sync_status TEXT DEFAULT 'pending',  -- 'pending', 'success', 'error'
                    error_message TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    source_connection TEXT,
                    target_connection TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar tabelas de sincronização: {str(e)}")
    
    def add_sync_table(self, table_name, description="", sync_type="full", primary_key="id"):
        """Adicionar tabela para sincronização de dados"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO data_sync_tables 
                (table_name, description, sync_type, primary_key_column, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (table_name, description, sync_type, primary_key))
            
            conn.commit()
            conn.close()
            
            self.logger.success(f"Tabela '{table_name}' adicionada para sincronização")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar tabela para sincronização: {str(e)}")
            return False
    
    def remove_sync_table(self, table_name):
        """Remover tabela da sincronização de dados"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            # Remover configurações de colunas
            cursor.execute("DELETE FROM data_sync_columns WHERE table_name = ?", (table_name,))
            
            # Remover tabela
            cursor.execute("DELETE FROM data_sync_tables WHERE table_name = ?", (table_name,))
            
            conn.commit()
            conn.close()
            
            self.logger.success(f"Tabela '{table_name}' removida da sincronização")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao remover tabela da sincronização: {str(e)}")
            return False
    
    def list_sync_tables(self):
        """Listar todas as tabelas configuradas para sincronização"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name, description, sync_type, primary_key_column, active, created_at
                FROM data_sync_tables
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'table_name': row[0],
                    'description': row[1] or 'Sem descrição',
                    'sync_type': row[2],
                    'primary_key': row[3],
                    'active': bool(row[4]),
                    'created_at': row[5]
                }
                for row in tables
            ]
            
        except Exception as e:
            self.logger.error(f"Erro ao listar tabelas de sincronização: {str(e)}")
            return []
    
    def get_active_sync_tables(self):
        """Obter apenas tabelas ativas para sincronização"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name, sync_type, primary_key_column
                FROM data_sync_tables
                WHERE active = 1
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'table_name': row[0],
                    'sync_type': row[1],
                    'primary_key': row[2]
                }
                for row in tables
            ]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter tabelas ativas: {str(e)}")
            return []
    
    def toggle_table_status(self, table_name):
        """Ativar/desativar uma tabela para sincronização"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            # Verificar status atual
            cursor.execute("SELECT active FROM data_sync_tables WHERE table_name = ?", (table_name,))
            result = cursor.fetchone()
            
            if not result:
                self.logger.error(f"Tabela '{table_name}' não encontrada")
                return False
            
            new_status = 0 if result[0] else 1
            cursor.execute(
                "UPDATE data_sync_tables SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE table_name = ?",
                (new_status, table_name)
            )
            
            conn.commit()
            conn.close()
            
            status_text = "ativada" if new_status else "desativada"
            self.logger.success(f"Tabela '{table_name}' {status_text}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao alterar status da tabela: {str(e)}")
            return False
    
    def configure_table_columns(self, table_name, source_connection):
        """Configurar colunas específicas de uma tabela para sincronização"""
        try:
            # Primeiro, obter estrutura da tabela do banco de origem
            from database.structure_analyzer import StructureAnalyzer
            analyzer = StructureAnalyzer(self.logger)
            structure = analyzer.analyze_database_structure(source_connection)
            
            if table_name not in structure['tables']:
                self.logger.error(f"Tabela '{table_name}' não encontrada no banco de origem")
                return False
            
            table_structure = structure['tables'][table_name]
            
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            # Limpar configurações existentes
            cursor.execute("DELETE FROM data_sync_columns WHERE table_name = ?", (table_name,))
            
            # Adicionar todas as colunas da tabela
            for column in table_structure['columns']:
                cursor.execute("""
                    INSERT INTO data_sync_columns 
                    (table_name, column_name, sync_enabled, is_key_column)
                    VALUES (?, ?, 1, ?)
                """, (table_name, column['name'], 1 if column['name'] == table_structure['primary_key'] else 0))
            
            conn.commit()
            conn.close()
            
            self.logger.success(f"Colunas da tabela '{table_name}' configuradas para sincronização")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar colunas: {str(e)}")
            return False
    
    def get_table_columns_config(self, table_name):
        """Obter configuração de colunas de uma tabela"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT column_name, sync_enabled, sync_direction, is_key_column
                FROM data_sync_columns
                WHERE table_name = ?
                ORDER BY column_name
            """, (table_name,))
            
            columns = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'column_name': row[0],
                    'sync_enabled': bool(row[1]),
                    'sync_direction': row[2],
                    'is_key_column': bool(row[3])
                }
                for row in columns
            ]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter configuração de colunas: {str(e)}")
            return []
    
    def update_column_config(self, table_name, column_name, sync_enabled=None, sync_direction=None):
        """Atualizar configuração específica de uma coluna"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if sync_enabled is not None:
                updates.append("sync_enabled = ?")
                params.append(1 if sync_enabled else 0)
            
            if sync_direction is not None:
                updates.append("sync_direction = ?")
                params.append(sync_direction)
            
            if not updates:
                return True
            
            params.extend([table_name, column_name])
            
            cursor.execute(f"""
                UPDATE data_sync_columns 
                SET {', '.join(updates)}
                WHERE table_name = ? AND column_name = ?
            """, params)
            
            conn.commit()
            conn.close()
            
            self.logger.success(f"Configuração da coluna '{column_name}' atualizada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar configuração de coluna: {str(e)}")
            return False
    
    def add_sync_history(self, table_name, sync_direction, source_conn, target_conn):
        """Adicionar registro de histórico de sincronização"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO data_sync_history 
                (table_name, sync_direction, source_connection, target_connection)
                VALUES (?, ?, ?, ?)
            """, (table_name, sync_direction, str(source_conn), str(target_conn)))
            
            history_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return history_id
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar histórico: {str(e)}")
            return None
    
    def update_sync_history(self, history_id, records_affected=None, status='success', error_message=None):
        """Atualizar registro de histórico de sincronização"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE data_sync_history 
                SET records_affected = ?, sync_status = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (records_affected, status, error_message, history_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar histórico: {str(e)}")
    
    def get_sync_history(self, table_name=None, limit=50):
        """Obter histórico de sincronizações"""
        try:
            conn = sqlite3.connect(self.config_db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT table_name, sync_direction, records_affected, sync_status, 
                       error_message, started_at, completed_at
                FROM data_sync_history
            """
            params = []
            
            if table_name:
                query += " WHERE table_name = ?"
                params.append(table_name)
            
            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            history = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'table_name': row[0],
                    'sync_direction': row[1],
                    'records_affected': row[2],
                    'sync_status': row[3],
                    'error_message': row[4],
                    'started_at': row[5],
                    'completed_at': row[6]
                }
                for row in history
            ]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico: {str(e)}")
            return []
