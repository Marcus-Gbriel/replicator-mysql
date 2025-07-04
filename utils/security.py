#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitários de validação e segurança
"""

import re
import pymysql
from colorama import Fore, Style

class SecurityValidator:
    def __init__(self, logger):
        """Inicializar validador de segurança"""
        self.logger = logger
        
        # Comandos perigosos que nunca devem ser executados
        self.dangerous_commands = [
            'DROP DATABASE', 'DROP SCHEMA', 'DELETE FROM', 'UPDATE SET',
            'TRUNCATE TABLE', 'DROP TABLE', 'GRANT ALL', 'REVOKE',
            'FLUSH PRIVILEGES', 'SHUTDOWN', 'KILL'
        ]
        
        # Padrões SQL suspeitos
        self.suspicious_patterns = [
            r';\s*DROP\s+', r';\s*DELETE\s+', r';\s*UPDATE\s+',
            r';\s*INSERT\s+', r';\s*TRUNCATE\s+', r'--\s*DROP'
        ]
    
    def validate_sql_command(self, sql_command):
        """Validar se um comando SQL é seguro"""
        sql_upper = sql_command.upper().strip()
        
        # Verificar comandos perigosos
        for dangerous in self.dangerous_commands:
            if dangerous in sql_upper:
                self.logger.error(f"Comando perigoso detectado: {dangerous}")
                return False
        
        # Verificar padrões suspeitos
        for pattern in self.suspicious_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                self.logger.error(f"Padrão suspeito detectado: {pattern}")
                return False
        
        # Comandos permitidos para alteração de estrutura
        allowed_starts = ['CREATE TABLE', 'ALTER TABLE', 'CREATE INDEX', 'SHOW CREATE']
        
        if not any(sql_upper.startswith(cmd) for cmd in allowed_starts):
            if not sql_upper.startswith(('SELECT', 'DESCRIBE', 'SHOW')):
                self.logger.warning(f"Comando não reconhecido como seguro: {sql_upper[:50]}...")
                return False
        
        return True
    
    def validate_connection_params(self, connection_details):
        """Validar parâmetros de conexão"""
        required_fields = ['host', 'port', 'username', 'password', 'database']
        
        for field in required_fields:
            if field not in connection_details or not connection_details[field]:
                self.logger.error(f"Campo obrigatório ausente: {field}")
                return False
        
        # Validar porta
        try:
            port = int(connection_details['port'])
            if not (1 <= port <= 65535):
                self.logger.error("Porta deve estar entre 1 e 65535")
                return False
        except ValueError:
            self.logger.error("Porta deve ser um número")
            return False
        
        # Validar nomes (sem caracteres perigosos)
        name_pattern = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
        
        if not name_pattern.match(connection_details['database']):
            self.logger.error("Nome do banco contém caracteres inválidos")
            return False
        
        if not name_pattern.match(connection_details['username']):
            self.logger.error("Nome de usuário contém caracteres inválidos")
            return False
        
        return True
    
    def check_database_permissions(self, connection_details):
        """Verificar se o usuário tem permissões adequadas"""
        try:
            connection = pymysql.connect(
                host=connection_details['host'],
                port=connection_details['port'],
                user=connection_details['username'],
                password=connection_details['password'],
                database=connection_details['database'],
                charset='utf8mb4'
            )
            
            permissions = {
                'select_info_schema': False,
                'alter_tables': False,
                'create_tables': False,
                'show_tables': False
            }
            
            with connection.cursor() as cursor:
                # Testar SELECT no information_schema
                try:
                    cursor.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s", 
                                 (connection_details['database'],))
                    cursor.fetchone()
                    permissions['select_info_schema'] = True
                except:
                    pass
                
                # Testar SHOW TABLES
                try:
                    cursor.execute("SHOW TABLES")
                    cursor.fetchall()
                    permissions['show_tables'] = True
                except:
                    pass
                
                # Verificar permissões específicas via GRANTS
                try:
                    cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
                    grants = cursor.fetchall()
                    
                    grants_text = ' '.join([grant[0] for grant in grants]).upper()
                    
                    if 'ALTER' in grants_text or 'ALL PRIVILEGES' in grants_text:
                        permissions['alter_tables'] = True
                    
                    if 'CREATE' in grants_text or 'ALL PRIVILEGES' in grants_text:
                        permissions['create_tables'] = True
                        
                except:
                    # Fallback: assumir permissões se não conseguir verificar
                    permissions['alter_tables'] = True
                    permissions['create_tables'] = True
            
            connection.close()
            
            # Relatório de permissões
            self.logger.info("Verificação de permissões:")
            for perm, status in permissions.items():
                status_str = "✓" if status else "✗"
                color = Fore.GREEN if status else Fore.RED
                self.logger.info(f"  {color}{status_str} {perm.replace('_', ' ').title()}{Style.RESET_ALL}")
            
            # Verificar se tem permissões mínimas
            required_perms = ['select_info_schema', 'show_tables']
            missing_perms = [p for p in required_perms if not permissions[p]]
            
            if missing_perms:
                self.logger.error(f"Permissões mínimas ausentes: {', '.join(missing_perms)}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar permissões: {str(e)}")
            return False
    
    def validate_table_name(self, table_name):
        """Validar nome de tabela"""
        # MySQL/MariaDB table name rules
        if not table_name:
            return False
        
        if len(table_name) > 64:
            return False
        
        # Permitir apenas caracteres alfanuméricos, underscore e alguns especiais
        pattern = re.compile(r'^[a-zA-Z0-9_$]+$')
        return pattern.match(table_name) is not None
    
    def validate_column_name(self, column_name):
        """Validar nome de coluna"""
        if not column_name:
            return False
        
        if len(column_name) > 64:
            return False
        
        # Permitir apenas caracteres alfanuméricos e underscore
        pattern = re.compile(r'^[a-zA-Z0-9_]+$')
        return pattern.match(column_name) is not None
    
    def is_safe_operation(self, operation_type, table_name, details=None):
        """Verificar se uma operação é considerada segura"""
        safe_operations = [
            'CREATE_TABLE', 'ADD_COLUMN', 'MODIFY_COLUMN', 
            'ADD_INDEX', 'ANALYZE_STRUCTURE'
        ]
        
        if operation_type not in safe_operations:
            self.logger.warning(f"Operação potencialmente insegura: {operation_type}")
            return False
        
        if not self.validate_table_name(table_name):
            self.logger.error(f"Nome de tabela inválido: {table_name}")
            return False
        
        return True
    
    def sanitize_identifier(self, identifier):
        """Limpar e validar identificador SQL"""
        # Remove espaços e caracteres perigosos
        cleaned = re.sub(r'[^\w]', '_', identifier)
        
        # Garante que não comece com número
        if cleaned and cleaned[0].isdigit():
            cleaned = 'col_' + cleaned
        
        # Limita o tamanho
        if len(cleaned) > 64:
            cleaned = cleaned[:64]
        
        return cleaned if cleaned else 'unnamed_field'
    
    def log_security_event(self, event_type, details, severity='INFO'):
        """Registrar evento de segurança"""
        security_msg = f"SECURITY [{severity}] {event_type}: {details}"
        
        if severity == 'ERROR':
            self.logger.error(security_msg)
        elif severity == 'WARNING':
            self.logger.warning(security_msg)
        else:
            self.logger.info(security_msg)
