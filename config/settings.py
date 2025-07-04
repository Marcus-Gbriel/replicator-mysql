#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações da aplicação
"""

import sqlite3
import os
from cryptography.fernet import Fernet
import json

class Settings:
    def __init__(self):
        """Inicializar configurações"""
        self.config_dir = "config"
        self.db_path = os.path.join(self.config_dir, "replicator.db")
        self.key_file = os.path.join(self.config_dir, "encryption.key")
        
        # Criar diretório de configuração se não existir
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Inicializar encriptação
        self._init_encryption()
        
        # Inicializar banco de dados
        self._init_database()
    
    def _init_encryption(self):
        """Inicializar sistema de encriptação"""
        if not os.path.exists(self.key_file):
            # Gerar nova chave
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        else:
            # Carregar chave existente
            with open(self.key_file, 'rb') as f:
                key = f.read()
        
        self.cipher = Fernet(key)
    
    def _init_database(self):
        """Inicializar banco de dados SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Criar tabela de conexões
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    database_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar tabela de configurações gerais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar tabela de logs de operações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    source_connection TEXT,
                    target_connection TEXT,
                    status TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def encrypt_password(self, password):
        """Encriptar senha"""
        return self.cipher.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password):
        """Descriptografar senha"""
        return self.cipher.decrypt(encrypted_password.encode()).decode()
    
    def save_connection(self, name, conn_type, host, port, username, password, database_name):
        """Salvar configuração de conexão"""
        encrypted_password = self.encrypt_password(password)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar se já existe uma conexão com o mesmo nome
            cursor.execute("SELECT id FROM connections WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                # Atualizar conexão existente
                cursor.execute('''
                    UPDATE connections 
                    SET type = ?, host = ?, port = ?, username = ?, 
                        password = ?, database_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (conn_type, host, port, username, encrypted_password, database_name, name))
            else:
                # Inserir nova conexão
                cursor.execute('''
                    INSERT INTO connections (name, type, host, port, username, password, database_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, conn_type, host, port, username, encrypted_password, database_name))
            
            conn.commit()
            return True
    
    def get_connection(self, connection_id):
        """Obter configuração de conexão por ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections WHERE id = ?", (connection_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'host': row[3],
                    'port': row[4],
                    'username': row[5],
                    'password': self.decrypt_password(row[6]),
                    'database': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
            return None
    
    def get_connection_by_name(self, name):
        """Obter configuração de conexão por nome"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'host': row[3],
                    'port': row[4],
                    'username': row[5],
                    'password': self.decrypt_password(row[6]),
                    'database': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
            return None
    
    def get_connection_by_type(self, conn_type):
        """Obter primeira conexão por tipo"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections WHERE type = ? LIMIT 1", (conn_type,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'host': row[3],
                    'port': row[4],
                    'username': row[5],
                    'password': self.decrypt_password(row[6]),
                    'database': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
            return None
    
    def get_all_connections(self):
        """Obter todas as conexões"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections ORDER BY name")
            rows = cursor.fetchall()
            
            connections = []
            for row in rows:
                connections.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'host': row[3],
                    'port': row[4],
                    'username': row[5],
                    'password': self.decrypt_password(row[6]),
                    'database': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                })
            
            return connections
    
    def delete_connection(self, connection_id):
        """Deletar conexão"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def log_operation(self, operation_type, source_connection=None, target_connection=None, 
                     status="SUCCESS", details=None):
        """Registrar operação no log"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_logs (operation_type, source_connection, target_connection, status, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (operation_type, source_connection, target_connection, status, details))
            conn.commit()
    
    def get_operation_logs(self, limit=50):
        """Obter logs de operações"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM operation_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'id': row[0],
                    'operation_type': row[1],
                    'source_connection': row[2],
                    'target_connection': row[3],
                    'status': row[4],
                    'details': row[5],
                    'created_at': row[6]
                })
            
            return logs
    
    def get_setting(self, key, default_value=None):
        """Obter configuração geral"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0]
            
            return default_value
    
    def set_setting(self, key, value):
        """Definir configuração geral"""
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value_str))
            conn.commit()
