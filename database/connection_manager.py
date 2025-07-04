#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de conexões com banco de dados
"""

import pymysql
from colorama import Fore, Style
from utils.menu import Menu

class ConnectionManager:
    def __init__(self, settings, logger):
        """Inicializar gerenciador de conexões"""
        self.settings = settings
        self.logger = logger
        self.menu = Menu(logger)
    
    def configure_source_connection(self):
        """Configurar conexão de origem (teste)"""
        self.logger.info("Iniciando configuração de conexão de origem")
        
        details = self.menu.get_connection_details("source")
        if details:
            success = self.settings.save_connection(
                details['name'], details['type'], details['host'],
                details['port'], details['username'], details['password'],
                details['database']
            )
            
            if success:
                self.logger.success(f"Conexão de origem '{details['name']}' configurada com sucesso")
                
                # Testar conexão imediatamente
                if self._test_connection_details(details):
                    self.logger.success("Teste de conexão bem-sucedido")
                else:
                    self.logger.warning("Falha no teste de conexão. Verifique os dados.")
            else:
                self.logger.error("Falha ao salvar configuração de conexão")
    
    def configure_target_connection(self):
        """Configurar conexão de destino (produção)"""
        self.logger.info("Iniciando configuração de conexão de destino")
        
        details = self.menu.get_connection_details("target")
        if details:
            success = self.settings.save_connection(
                details['name'], details['type'], details['host'],
                details['port'], details['username'], details['password'],
                details['database']
            )
            
            if success:
                self.logger.success(f"Conexão de destino '{details['name']}' configurada com sucesso")
                
                # Testar conexão imediatamente
                if self._test_connection_details(details):
                    self.logger.success("Teste de conexão bem-sucedido")
                else:
                    self.logger.warning("Falha no teste de conexão. Verifique os dados.")
            else:
                self.logger.error("Falha ao salvar configuração de conexão")
    
    def list_connections(self):
        """Listar todas as conexões"""
        connections = self.settings.get_all_connections()
        self.menu.display_connections(connections)
    
    def delete_connection(self):
        """Deletar uma conexão"""
        connections = self.settings.get_all_connections()
        
        if not connections:
            print(f"{Fore.YELLOW}Nenhuma conexão configurada para deletar.{Style.RESET_ALL}")
            return
        
        selected_conn = self.menu.select_connection(connections, "Selecione a conexão para deletar")
        
        if selected_conn:
            confirm = input(f"\n{Fore.RED}Tem certeza que deseja deletar a conexão '{selected_conn['name']}'? (s/N): {Style.RESET_ALL}").strip().lower()
            
            if confirm == 's':
                if self.settings.delete_connection(selected_conn['id']):
                    self.logger.success(f"Conexão '{selected_conn['name']}' deletada com sucesso")
                else:
                    self.logger.error("Falha ao deletar conexão")
            else:
                print(f"{Fore.YELLOW}Operação cancelada.{Style.RESET_ALL}")
    
    def test_connection(self, connection_id):
        """Testar uma conexão específica"""
        connection = self.settings.get_connection(connection_id)
        if not connection:
            self.logger.error(f"Conexão com ID {connection_id} não encontrada")
            return False
        
        return self._test_connection_details(connection)
    
    def _test_connection_details(self, connection_details):
        """Testar conexão com detalhes fornecidos"""
        try:
            self.logger.info(f"Testando conexão com {connection_details['host']}:{connection_details['port']}")
            
            # Tentar conectar
            connection = pymysql.connect(
                host=connection_details['host'],
                port=connection_details['port'],
                user=connection_details['username'],
                password=connection_details['password'],
                database=connection_details['database'],
                charset='utf8mb4',
                connect_timeout=10
            )
            
            # Testar uma query simples
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                self.logger.info(f"Conectado ao MySQL/MariaDB versão: {version}")
            
            connection.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Falha na conexão: {str(e)}")
            return False
    
    def get_connection(self, connection_id):
        """Obter conexão por ID"""
        return self.settings.get_connection(connection_id)
    
    def get_connection_by_type(self, conn_type):
        """Obter conexão por tipo"""
        return self.settings.get_connection_by_type(conn_type)
    
    def get_all_connections(self):
        """Obter todas as conexões"""
        return self.settings.get_all_connections()
    
    def create_connection(self, connection_details):
        """Criar conexão PyMySQL"""
        try:
            connection = pymysql.connect(
                host=connection_details['host'],
                port=connection_details['port'],
                user=connection_details['username'],
                password=connection_details['password'],
                database=connection_details['database'],
                charset='utf8mb4',
                autocommit=False  # Para controle manual de transações
            )
            
            return connection
            
        except Exception as e:
            self.logger.error(f"Erro ao criar conexão: {str(e)}")
            return None
    
    def execute_query(self, connection_details, query, params=None):
        """Executar query com segurança"""
        connection = None
        try:
            connection = self.create_connection(connection_details)
            if not connection:
                return None
            
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                
                # Se é uma query SELECT, retornar resultados
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    # Para outras queries, confirmar transação
                    connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            if connection:
                connection.rollback()
            self.logger.error(f"Erro ao executar query: {str(e)}")
            return None
        
        finally:
            if connection:
                connection.close()
    
    def get_database_info(self, connection_details):
        """Obter informações do banco de dados"""
        try:
            connection = self.create_connection(connection_details)
            if not connection:
                return None
            
            info = {}
            
            with connection.cursor() as cursor:
                # Versão do MySQL/MariaDB
                cursor.execute("SELECT VERSION()")
                info['version'] = cursor.fetchone()[0]
                
                # Nome do banco
                cursor.execute("SELECT DATABASE()")
                info['database'] = cursor.fetchone()[0]
                
                # Charset do banco
                cursor.execute("SELECT DEFAULT_CHARACTER_SET_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s", (info['database'],))
                result = cursor.fetchone()
                info['charset'] = result[0] if result else 'unknown'
                
                # Número de tabelas
                cursor.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s", (info['database'],))
                info['table_count'] = cursor.fetchone()[0]
            
            connection.close()
            return info
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do banco: {str(e)}")
            return None
