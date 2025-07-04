#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL/MariaDB Structure Replicator
Aplicação para replicação segura de estrutura de banco de dados
"""

import os
import sys
from colorama import Fore, Style, init
from config.settings import Settings
from utils.menu import Menu
from utils.logger import Logger
from database.connection_manager import ConnectionManager
from database.structure_analyzer import StructureAnalyzer
from database.replicator import Replicator
from utils.data_sync_menu import DataSyncMenu

# Inicializar colorama para Windows
init(autoreset=True)

class DatabaseReplicatorApp:
    def __init__(self):
        """Inicializar aplicação"""
        self.settings = Settings()
        self.logger = Logger()
        self.connection_manager = ConnectionManager(self.settings, self.logger)
        self.structure_analyzer = StructureAnalyzer(self.logger)
        self.replicator = Replicator(self.logger)
        self.menu = Menu(self.logger)
        self.data_sync_menu = DataSyncMenu(self.logger, self.connection_manager)
        
        # Criar diretórios necessários
        self._create_directories()
        
    def _create_directories(self):
        """Criar diretórios necessários"""
        directories = ['logs', 'backups', 'config']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def run(self):
        """Executar aplicação principal"""
        try:
            while True:
                choice = self.menu.show_main_menu()
                
                if choice == '1':
                    self._configure_connections()
                elif choice == '2':
                    self._test_connections()
                elif choice == '3':
                    self._diagnose_connections()
                elif choice == '4':
                    self._analyze_structures()
                elif choice == '5':
                    self._replicate_structure()
                elif choice == '6':
                    self._data_synchronization()
                elif choice == '7':
                    self._view_logs()
                elif choice == '8':
                    self._backup_management()
                elif choice == '0':
                    self._exit_application()
                    break
                else:
                    self.menu.clear_screen()
                    self.menu.show_header()
                    print(f"{Fore.RED}Opção inválida! Tente novamente.{Style.RESET_ALL}")
                
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            self.menu.clear_screen()
            print(f"\n{Fore.YELLOW}Aplicação interrompida pelo usuário.{Style.RESET_ALL}")
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            self.menu.clear_screen()
            print(f"{Fore.RED}Erro inesperado: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def _configure_connections(self):
        """Configurar conexões de banco"""
        self.menu.clear_screen()
        self.menu.show_header()
        
        choice = self.menu.show_connection_menu()
        
        if choice == '1':
            self.connection_manager.configure_source_connection()
        elif choice == '2':
            self.connection_manager.configure_target_connection()
        elif choice == '3':
            self.connection_manager.list_connections()
        elif choice == '4':
            self.connection_manager.delete_connection()
    
    def _test_connections(self):
        """Testar conexões configuradas"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== TESTE DE CONEXÕES ==={Style.RESET_ALL}")
        
        connections = self.connection_manager.get_all_connections()
        if not connections:
            print(f"{Fore.YELLOW}Nenhuma conexão configurada.{Style.RESET_ALL}")
            return
        
        for conn in connections:
            print(f"\n{Fore.CYAN}Testando conexão: {conn['name']}{Style.RESET_ALL}")
            if self.connection_manager.test_connection(conn['id']):
                print(f"{Fore.GREEN}✓ Conexão bem-sucedida{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Falha na conexão{Style.RESET_ALL}")
    
    def _diagnose_connections(self):
        """Diagnosticar problemas nas conexões"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== DIAGNÓSTICO DE CONEXÕES ==={Style.RESET_ALL}")
        
        source_conn = self.connection_manager.get_connection_by_type('source')
        target_conn = self.connection_manager.get_connection_by_type('target')
        
        if not source_conn:
            print(f"{Fore.RED}❌ Conexão de origem não configurada{Style.RESET_ALL}")
            return False
        
        if not target_conn:
            print(f"{Fore.RED}❌ Conexão de destino não configurada{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.CYAN}Testando conexão de origem...{Style.RESET_ALL}")
        if self.connection_manager.test_connection(source_conn['id']):
            print(f"{Fore.GREEN}✓ Conexão de origem OK{Style.RESET_ALL}")
            
            # Verificar se tem tabelas
            source_info = self.connection_manager.get_database_info(source_conn)
            if source_info:
                print(f"  📊 Tabelas encontradas: {source_info['table_count']}")
                print(f"  🗄️  Versão: {source_info['version']}")
            
        else:
            print(f"{Fore.RED}❌ Falha na conexão de origem{Style.RESET_ALL}")
            return False
        
        print(f"\n{Fore.CYAN}Testando conexão de destino...{Style.RESET_ALL}")
        if self.connection_manager.test_connection(target_conn['id']):
            print(f"{Fore.GREEN}✓ Conexão de destino OK{Style.RESET_ALL}")
            
            # Verificar se tem tabelas
            target_info = self.connection_manager.get_database_info(target_conn)
            if target_info:
                print(f"  📊 Tabelas encontradas: {target_info['table_count']}")
                print(f"  🗄️  Versão: {target_info['version']}")
                
                if target_info['table_count'] == 0:
                    print(f"  {Fore.YELLOW}⚠️  Banco de destino está vazio - todas as tabelas serão criadas{Style.RESET_ALL}")
            
        else:
            print(f"{Fore.RED}❌ Falha na conexão de destino{Style.RESET_ALL}")
            return False
        
        print(f"\n{Fore.GREEN}✓ Todas as conexões estão funcionais{Style.RESET_ALL}")
        return True

    def _analyze_structures(self):
        """Analisar estruturas dos bancos"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== ANÁLISE DE ESTRUTURAS ==={Style.RESET_ALL}")
        
        # Obter conexões de origem e destino
        source_conn = self.connection_manager.get_connection_by_type('source')
        target_conn = self.connection_manager.get_connection_by_type('target')
        
        if not source_conn or not target_conn:
            print(f"{Fore.RED}Configure as conexões de origem e destino primeiro.{Style.RESET_ALL}")
            return
        
        # Analisar estruturas
        source_structure = self.structure_analyzer.analyze_database_structure(source_conn)
        target_structure = self.structure_analyzer.analyze_database_structure(target_conn)
        
        if source_structure and target_structure:
            differences = self.structure_analyzer.compare_structures(source_structure, target_structure)
            self.structure_analyzer.display_differences(differences)
    
    def _replicate_structure(self):
        """Executar replicação de estrutura"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== REPLICAÇÃO DE ESTRUTURA ==={Style.RESET_ALL}")
        
        # Verificar se há conexões configuradas
        source_conn = self.connection_manager.get_connection_by_type('source')
        target_conn = self.connection_manager.get_connection_by_type('target')
        
        if not source_conn or not target_conn:
            print(f"{Fore.RED}Configure as conexões de origem e destino primeiro.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Use a opção 1 (Configurar Conexões) para configurar ambos os bancos.{Style.RESET_ALL}")
            return
        
        # Fazer diagnóstico rápido
        print(f"{Fore.CYAN}Fazendo verificação prévia...{Style.RESET_ALL}")
        
        # Testar conexões
        if not self.connection_manager.test_connection(source_conn['id']):
            print(f"{Fore.RED}❌ Falha na conexão com banco de origem. Verifique as configurações.{Style.RESET_ALL}")
            return
        
        if not self.connection_manager.test_connection(target_conn['id']):
            print(f"{Fore.RED}❌ Falha na conexão com banco de destino. Verifique as configurações.{Style.RESET_ALL}")
            return
        
        # Verificar se origem tem tabelas
        source_info = self.connection_manager.get_database_info(source_conn)
        if source_info and source_info['table_count'] == 0:
            print(f"{Fore.RED}❌ O banco de origem não possui tabelas para replicar.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Verifique se o banco '{source_conn['database']}' está correto.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✓ Verificações iniciais OK{Style.RESET_ALL}")
        
        # Confirmar operação
        print(f"\n{Fore.YELLOW}ATENÇÃO: Esta operação irá replicar a estrutura do banco de origem para o destino.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Um backup será criado automaticamente antes de qualquer alteração.{Style.RESET_ALL}")
        
        confirm = input(f"\n{Fore.CYAN}Deseja continuar? (s/N): {Style.RESET_ALL}").strip().lower()
        if confirm != 's':
            print(f"{Fore.YELLOW}Operação cancelada.{Style.RESET_ALL}")
            return
        
        # Executar replicação
        try:
            success = self.replicator.replicate_structure(source_conn, target_conn)
            
            if success:
                print(f"\n{Fore.GREEN}✓ Replicação concluída com sucesso!{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}✗ Falha na replicação. Verifique os logs para detalhes.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Use a opção 6 (Visualizar Logs) para ver mais informações.{Style.RESET_ALL}")
        except Exception as e:
            self.logger.error(f"Erro durante replicação: {str(e)}")
            print(f"\n{Fore.RED}✗ Erro inesperado durante replicação: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Verifique os logs para mais detalhes.{Style.RESET_ALL}")
    
    def _view_logs(self):
        """Visualizar logs"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== VISUALIZAÇÃO DE LOGS ==={Style.RESET_ALL}")
        self.logger.display_recent_logs()
    
    def _backup_management(self):
        """Gerenciar backups"""
        self.menu.clear_screen()
        self.menu.show_header()
        
        choice = self.menu.show_backup_menu()
        
        if choice == '1':
            self._create_manual_backup()
        elif choice == '2':
            self._list_backups()
        elif choice == '3':
            self._restore_backup()
    
    def _create_manual_backup(self):
        """Criar backup manual"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== CRIAR BACKUP MANUAL ==={Style.RESET_ALL}")
        
        connections = self.connection_manager.get_all_connections()
        if not connections:
            print(f"{Fore.YELLOW}Nenhuma conexão configurada.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Selecione a conexão para backup:{Style.RESET_ALL}")
        for i, conn in enumerate(connections):
            print(f"{i+1}. {conn['name']} ({conn['type']})")
        
        try:
            choice = int(input(f"\n{Fore.CYAN}Escolha (1-{len(connections)}): {Style.RESET_ALL}"))
            if 1 <= choice <= len(connections):
                selected_conn = connections[choice-1]
                success = self.replicator.create_backup(selected_conn)
                if success:
                    print(f"{Fore.GREEN}✓ Backup criado com sucesso!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Falha ao criar backup.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Opção inválida.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Entrada inválida.{Style.RESET_ALL}")
    
    def _list_backups(self):
        """Listar backups disponíveis"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== BACKUPS DISPONÍVEIS ==={Style.RESET_ALL}")
        
        backups = self.replicator.list_backups()
        if not backups:
            print(f"{Fore.YELLOW}Nenhum backup encontrado.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Backups disponíveis:{Style.RESET_ALL}")
        for backup in backups:
            print(f"• {backup}")
    
    def _restore_backup(self):
        """Restaurar backup"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}=== RESTAURAR BACKUP ==={Style.RESET_ALL}")
        
        print(f"{Fore.YELLOW}Funcionalidade de restauração será implementada em versão futura.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Por segurança, use ferramentas específicas do MySQL/MariaDB para restauração.{Style.RESET_ALL}")
    
    def _data_synchronization(self):
        """Menu de sincronização de dados"""
        self.data_sync_menu.show_data_sync_menu()
    
    def _exit_application(self):
        """Sair da aplicação"""
        self.menu.clear_screen()
        self.menu.show_header()
        print(f"{Fore.GREEN}Obrigado por usar o MySQL/MariaDB Structure Replicator!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Todos os logs foram salvos para futuras consultas.{Style.RESET_ALL}")

def main():
    """Função principal"""
    try:
        app = DatabaseReplicatorApp()
        app.run()
    except Exception as e:
        print(f"{Fore.RED}Erro fatal: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
