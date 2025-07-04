#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface para configuração de sincronização de dados
"""

import os
from colorama import Fore, Style
from tabulate import tabulate
from config.data_sync_config import DataSyncConfig
from database.data_synchronizer import DataSynchronizer

class DataSyncMenu:
    def __init__(self, logger, connection_manager):
        """Inicializar menu de sincronização de dados"""
        self.logger = logger
        self.connection_manager = connection_manager
        self.config = DataSyncConfig(logger)
        self.synchronizer = DataSynchronizer(logger)
    
    def clear_screen(self):
        """Limpar a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Mostrar cabeçalho da aplicação"""
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}{'  MySQL/MariaDB STRUCTURE REPLICATOR':^70}")
        print(f"{Fore.CYAN}{'  Sincronização de Dados Entre Ambientes':^70}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    def show_data_sync_menu(self):
        """Exibir menu principal de sincronização de dados"""
        while True:
            self.clear_screen()
            self.show_header()
            
            print(f"{Fore.GREEN}=== SINCRONIZAÇÃO DE DADOS ==={Style.RESET_ALL}")
            
            options = [
                ["1", "Configurar Tabelas", "Adicionar/remover tabelas para sincronização"],
                ["2", "Listar Configurações", "Ver tabelas configuradas para sincronização"],
                ["3", "Configurar Colunas", "Configurar colunas específicas de uma tabela"],
                ["4", "Sincronizar Dados", "Executar sincronização de dados"],
                ["5", "Sincronizar Tabela", "Sincronizar uma tabela específica"],
                ["6", "Histórico", "Ver histórico de sincronizações"],
                ["7", "Ativar/Desativar", "Ativar ou desativar tabela para sincronização"],
                ["0", "Voltar", "Retornar ao menu principal"]
            ]
            
            print(tabulate(options, headers=["Opção", "Ação", "Descrição"], 
                          tablefmt="grid", colalign=("center", "left", "left")))
            
            choice = input(f"\n{Fore.CYAN}Escolha uma opção (0-7): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._configure_tables_menu()
            elif choice == "2":
                self._list_configurations()
            elif choice == "3":
                self._configure_columns_menu()
            elif choice == "4":
                self._sync_data_menu()
            elif choice == "5":
                self._sync_single_table_menu()
            elif choice == "6":
                self._show_history()
            elif choice == "7":
                self._toggle_table_menu()
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _configure_tables_menu(self):
        """Menu para configurar tabelas"""
        while True:
            self.clear_screen()
            self.show_header()
            
            print(f"{Fore.GREEN}=== CONFIGURAÇÃO DE TABELAS ==={Style.RESET_ALL}")
            
            options = [
                ["1", "Adicionar Tabela", "Adicionar nova tabela para sincronização"],
                ["2", "Remover Tabela", "Remover tabela da sincronização"],
                ["3", "Listar Tabelas", "Ver tabelas do banco de origem"],
                ["0", "Voltar", "Retornar ao menu anterior"]
            ]
            
            print(tabulate(options, headers=["Opção", "Ação", "Descrição"], 
                          tablefmt="grid", colalign=("center", "left", "left")))
            
            choice = input(f"\n{Fore.CYAN}Escolha uma opção (0-3): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._add_table_to_sync()
            elif choice == "2":
                self._remove_table_from_sync()
            elif choice == "3":
                self._list_database_tables()
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _add_table_to_sync(self):
        """Adicionar tabela para sincronização"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== ADICIONAR TABELA PARA SINCRONIZAÇÃO ==={Style.RESET_ALL}")
            
            # Verificar se as conexões estão configuradas
            source_conn = self.connection_manager.get_connection_by_type('source')
            if not source_conn:
                print(f"{Fore.RED}✗ Conexão de origem não configurada{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            # Listar tabelas disponíveis
            self._show_available_tables(source_conn)
            
            table_name = input(f"\n{Fore.CYAN}Nome da tabela: {Style.RESET_ALL}").strip()
            if not table_name:
                print(f"{Fore.RED}Nome da tabela é obrigatório{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            description = input(f"{Fore.CYAN}Descrição (opcional): {Style.RESET_ALL}").strip()
            
            print(f"\n{Fore.YELLOW}Tipos de sincronização disponíveis:{Style.RESET_ALL}")
            print(f"  {Fore.GREEN}1{Style.RESET_ALL} - Full (completa - substitui todos os dados)")
            print(f"  {Fore.GREEN}2{Style.RESET_ALL} - Incremental (apenas novos/modificados)")
            print(f"  {Fore.GREEN}3{Style.RESET_ALL} - Key Only (apenas chaves/registros novos)")
            
            sync_choice = input(f"\n{Fore.CYAN}Tipo de sincronização (1-3): {Style.RESET_ALL}").strip()
            sync_types = {"1": "full", "2": "incremental", "3": "key_only"}
            sync_type = sync_types.get(sync_choice, "full")
            
            primary_key = input(f"{Fore.CYAN}Coluna de chave primária (padrão: id): {Style.RESET_ALL}").strip() or "id"
            
            # Adicionar tabela
            if self.config.add_sync_table(table_name, description, sync_type, primary_key):
                # Configurar colunas automaticamente
                if self.config.configure_table_columns(table_name, source_conn):
                    print(f"\n{Fore.GREEN}✓ Tabela '{table_name}' configurada com sucesso!{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.YELLOW}⚠ Tabela adicionada, mas houve erro na configuração de colunas{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}✗ Erro ao adicionar tabela{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _remove_table_from_sync(self):
        """Remover tabela da sincronização"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== REMOVER TABELA DA SINCRONIZAÇÃO ==={Style.RESET_ALL}")
            
            # Listar tabelas configuradas
            sync_tables = self.config.list_sync_tables()
            
            if not sync_tables:
                print(f"{Fore.YELLOW}Nenhuma tabela configurada para sincronização{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            print(f"\n{Fore.CYAN}Tabelas configuradas:{Style.RESET_ALL}")
            for i, table in enumerate(sync_tables, 1):
                status = "Ativa" if table['active'] else "Inativa"
                print(f"  {Fore.GREEN}{i}{Style.RESET_ALL} - {table['table_name']} ({status})")
            
            choice = input(f"\n{Fore.CYAN}Escolha a tabela para remover (1-{len(sync_tables)}): {Style.RESET_ALL}").strip()
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(sync_tables):
                    table_name = sync_tables[index]['table_name']
                    
                    confirm = input(f"\n{Fore.YELLOW}Confirma a remoção da tabela '{table_name}'? (s/N): {Style.RESET_ALL}").strip().lower()
                    if confirm == 's':
                        if self.config.remove_sync_table(table_name):
                            print(f"\n{Fore.GREEN}✓ Tabela '{table_name}' removida com sucesso!{Style.RESET_ALL}")
                        else:
                            print(f"\n{Fore.RED}✗ Erro ao remover tabela{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.YELLOW}Operação cancelada{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.RED}Opção inválida{Style.RESET_ALL}")
            except ValueError:
                print(f"\n{Fore.RED}Por favor, digite um número válido{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _show_available_tables(self, source_connection):
        """Mostrar tabelas disponíveis no banco de origem"""
        try:
            from database.structure_analyzer import StructureAnalyzer
            analyzer = StructureAnalyzer(self.logger)
            structure = analyzer.analyze_database_structure(source_connection)
            
            if structure and structure['tables']:
                print(f"\n{Fore.CYAN}Tabelas disponíveis no banco de origem:{Style.RESET_ALL}")
                tables = list(structure['tables'].keys())
                
                # Mostrar em colunas
                cols = 3
                for i in range(0, len(tables), cols):
                    row_tables = tables[i:i+cols]
                    row_str = "  ".join(f"{table:<25}" for table in row_tables)
                    print(f"  {row_str}")
            else:
                print(f"\n{Fore.YELLOW}Nenhuma tabela encontrada no banco de origem{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"\n{Fore.RED}Erro ao listar tabelas: {str(e)}{Style.RESET_ALL}")
    
    def _list_database_tables(self):
        """Listar tabelas do banco de dados"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== TABELAS DO BANCO DE ORIGEM ==={Style.RESET_ALL}")
            
            source_conn = self.connection_manager.get_connection_by_type('source')
            if not source_conn:
                print(f"{Fore.RED}✗ Conexão de origem não configurada{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            self._show_available_tables(source_conn)
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _list_configurations(self):
        """Listar tabelas configuradas"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== TABELAS CONFIGURADAS ==={Style.RESET_ALL}")
            
            sync_tables = self.config.list_sync_tables()
            
            if not sync_tables:
                print(f"{Fore.YELLOW}Nenhuma tabela configurada para sincronização{Style.RESET_ALL}")
            else:
                # Preparar dados para tabela
                table_data = []
                for table in sync_tables:
                    status = "Ativa" if table['active'] else "Inativa"
                    table_data.append([
                        table['table_name'],
                        status,
                        table['sync_type'],
                        table['primary_key'],
                        table['description'][:30] + "..." if len(table['description']) > 30 else table['description']
                    ])
                
                print(tabulate(table_data, 
                             headers=["Tabela", "Status", "Tipo", "Chave", "Descrição"],
                             tablefmt="grid"))
                
                print(f"\n{Fore.CYAN}Total: {len(sync_tables)} tabelas configuradas{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _configure_columns_menu(self):
        """Menu para configurar colunas específicas"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== CONFIGURAR COLUNAS DE TABELA ==={Style.RESET_ALL}")
            
            sync_tables = self.config.list_sync_tables()
            
            if not sync_tables:
                print(f"{Fore.YELLOW}Nenhuma tabela configurada para sincronização{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            # Mostrar tabelas em formato de tabela
            table_data = []
            for i, table in enumerate(sync_tables, 1):
                status = "Ativa" if table['active'] else "Inativa"
                table_data.append([str(i), table['table_name'], status])
            
            print(tabulate(table_data, headers=["#", "Tabela", "Status"], 
                          tablefmt="grid", colalign=("center", "left", "center")))
            
            choice = input(f"\n{Fore.CYAN}Escolha a tabela (1-{len(sync_tables)}): {Style.RESET_ALL}").strip()
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(sync_tables):
                    table_name = sync_tables[index]['table_name']
                    self._show_table_columns_config(table_name)
                else:
                    print(f"\n{Fore.RED}Opção inválida{Style.RESET_ALL}")
            except ValueError:
                print(f"\n{Fore.RED}Por favor, digite um número válido{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _show_table_columns_config(self, table_name):
        """Mostrar configuração de colunas de uma tabela"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== CONFIGURAÇÃO DE COLUNAS: {table_name} ==={Style.RESET_ALL}")
            
            columns = self.config.get_table_columns_config(table_name)
            
            if not columns:
                print(f"{Fore.YELLOW}Nenhuma coluna configurada para esta tabela{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            # Preparar dados para tabela
            column_data = []
            for i, col in enumerate(columns, 1):
                sync_status = "Sim" if col['sync_enabled'] else "Não"
                key_status = "Sim" if col['is_key_column'] else "Não"
                column_data.append([
                    str(i),
                    col['column_name'],
                    sync_status,
                    col['sync_direction'],
                    key_status
                ])
            
            print(tabulate(column_data, 
                          headers=["#", "Coluna", "Sincronizar", "Direção", "Chave"],
                          tablefmt="grid", colalign=("center", "left", "center", "center", "center")))
            
            # Opção para modificar configuração
            modify = input(f"\n{Fore.CYAN}Deseja modificar alguma coluna? (s/N): {Style.RESET_ALL}").strip().lower()
            if modify == 's':
                self._modify_column_config(table_name, columns)
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
            input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _modify_column_config(self, table_name, columns):
        """Modificar configuração de uma coluna"""
        try:
            choice = input(f"\n{Fore.CYAN}Número da coluna para modificar (1-{len(columns)}): {Style.RESET_ALL}").strip()
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(columns):
                    column = columns[index]
                    column_name = column['column_name']
                    
                    print(f"\n{Fore.GREEN}=== CONFIGURANDO COLUNA: {column_name} ==={Style.RESET_ALL}")
                    print(f"Status atual: {'Ativa' if column['sync_enabled'] else 'Inativa'}")
                    print(f"Direção atual: {column['sync_direction']}")
                    
                    # Alterar status de sincronização
                    enable = input(f"\n{Fore.CYAN}Sincronizar esta coluna? (s/n): {Style.RESET_ALL}").strip().lower()
                    sync_enabled = enable == 's'
                    
                    # Alterar direção
                    if sync_enabled:
                        direction_options = [
                            ["1", "both", "Ambas as direções"],
                            ["2", "to_prod", "Apenas para produção"],
                            ["3", "to_dev", "Apenas para desenvolvimento"]
                        ]
                        
                        print(f"\n{Fore.CYAN}Direções disponíveis:{Style.RESET_ALL}")
                        print(tabulate(direction_options, headers=["Opção", "Código", "Descrição"], 
                                      tablefmt="grid", colalign=("center", "left", "left")))
                        
                        dir_choice = input(f"\n{Fore.CYAN}Escolha a direção (1-3): {Style.RESET_ALL}").strip()
                        directions = {"1": "both", "2": "to_prod", "3": "to_dev"}
                        sync_direction = directions.get(dir_choice, "both")
                    else:
                        sync_direction = column['sync_direction']  # Manter atual
                    
                    # Atualizar configuração
                    if self.config.update_column_config(table_name, column_name, sync_enabled, sync_direction):
                        print(f"\n{Fore.GREEN}✓ Configuração atualizada com sucesso!{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.RED}✗ Erro ao atualizar configuração{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.RED}Opção inválida{Style.RESET_ALL}")
            except ValueError:
                print(f"\n{Fore.RED}Por favor, digite um número válido{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _sync_data_menu(self):
        """Menu para sincronizar dados"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== SINCRONIZAÇÃO DE DADOS ==={Style.RESET_ALL}")
            
            # Verificar conexões
            if not self._check_connections():
                return
            
            # Mostrar tabelas que serão sincronizadas
            active_tables = self.config.get_active_sync_tables()
            
            if not active_tables:
                print(f"{Fore.YELLOW}Nenhuma tabela ativa para sincronização{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            # Mostrar tabelas em formato de tabela
            table_data = []
            for table in active_tables:
                table_data.append([table['table_name'], table['sync_type']])
            
            print(f"\n{Fore.CYAN}Tabelas que serão sincronizadas:{Style.RESET_ALL}")
            print(tabulate(table_data, headers=["Tabela", "Tipo de Sincronização"], 
                          tablefmt="grid", colalign=("left", "center")))
            
            # Opções de direção
            direction_options = [
                ["1", "Homologação → Produção", "Sincronizar do ambiente de teste para produção"],
                ["2", "Produção → Homologação", "Sincronizar da produção para ambiente de teste"]
            ]
            
            print(f"\n{Fore.CYAN}Direções disponíveis:{Style.RESET_ALL}")
            print(tabulate(direction_options, headers=["Opção", "Direção", "Descrição"], 
                          tablefmt="grid", colalign=("center", "left", "left")))
            
            direction_choice = input(f"\n{Fore.CYAN}Escolha a direção (1-2): {Style.RESET_ALL}").strip()
            
            if direction_choice == "1":
                direction = "to_prod"
                source_conn = self.connection_manager.get_connection_by_type('source')
                target_conn = self.connection_manager.get_connection_by_type('target')
                direction_text = "Homologação → Produção"
            elif direction_choice == "2":
                direction = "to_dev"
                source_conn = self.connection_manager.get_connection_by_type('target')
                target_conn = self.connection_manager.get_connection_by_type('source')
                direction_text = "Produção → Homologação"
            else:
                print(f"\n{Fore.RED}Opção inválida{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            # Confirmação
            confirm = input(f"\n{Fore.YELLOW}Confirma a sincronização {direction_text}? (s/N): {Style.RESET_ALL}").strip().lower()
            
            if confirm == 's':
                print(f"\n{Fore.CYAN}Iniciando sincronização...{Style.RESET_ALL}")
                success = self.synchronizer.sync_all_configured_tables(source_conn, target_conn, direction)
                
                if success:
                    print(f"\n{Fore.GREEN}✓ Sincronização concluída com sucesso!{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.RED}✗ Sincronização concluída com erros{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.YELLOW}Sincronização cancelada{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _sync_single_table_menu(self):
        """Menu para sincronizar uma tabela específica"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== SINCRONIZAR TABELA ESPECÍFICA ==={Style.RESET_ALL}")
            
            # Verificar conexões
            if not self._check_connections():
                return
            
            active_tables = self.config.get_active_sync_tables()
            
            if not active_tables:
                print(f"{Fore.YELLOW}Nenhuma tabela ativa para sincronização{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            # Mostrar tabelas disponíveis
            table_data = []
            for i, table in enumerate(active_tables, 1):
                table_data.append([str(i), table['table_name'], table['sync_type']])
            
            print(f"\n{Fore.CYAN}Tabelas disponíveis:{Style.RESET_ALL}")
            print(tabulate(table_data, headers=["#", "Tabela", "Tipo"], 
                          tablefmt="grid", colalign=("center", "left", "center")))
            
            choice = input(f"\n{Fore.CYAN}Escolha a tabela (1-{len(active_tables)}): {Style.RESET_ALL}").strip()
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(active_tables):
                    table_name = active_tables[index]['table_name']
                    
                    # Opções de direção
                    direction_options = [
                        ["1", "Homologação → Produção", "Sincronizar do ambiente de teste para produção"],
                        ["2", "Produção → Homologação", "Sincronizar da produção para ambiente de teste"]
                    ]
                    
                    print(f"\n{Fore.CYAN}Direções disponíveis:{Style.RESET_ALL}")
                    print(tabulate(direction_options, headers=["Opção", "Direção", "Descrição"], 
                                  tablefmt="grid", colalign=("center", "left", "left")))
                    
                    direction_choice = input(f"\n{Fore.CYAN}Escolha a direção (1-2): {Style.RESET_ALL}").strip()
                    
                    if direction_choice == "1":
                        direction = "to_prod"
                        source_conn = self.connection_manager.get_connection_by_type('source')
                        target_conn = self.connection_manager.get_connection_by_type('target')
                        direction_text = "Homologação → Produção"
                    elif direction_choice == "2":
                        direction = "to_dev"
                        source_conn = self.connection_manager.get_connection_by_type('target')
                        target_conn = self.connection_manager.get_connection_by_type('source')
                        direction_text = "Produção → Homologação"
                    else:
                        print(f"\n{Fore.RED}Opção inválida{Style.RESET_ALL}")
                        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                        return
                    
                    # Confirmação
                    confirm = input(f"\n{Fore.YELLOW}Confirma a sincronização da tabela '{table_name}' ({direction_text})? (s/N): {Style.RESET_ALL}").strip().lower()
                    
                    if confirm == 's':
                        print(f"\n{Fore.CYAN}Sincronizando tabela {table_name}...{Style.RESET_ALL}")
                        success = self.synchronizer.sync_single_table(table_name, source_conn, target_conn, direction)
                        
                        if success:
                            print(f"\n{Fore.GREEN}✓ Sincronização da tabela '{table_name}' concluída com sucesso!{Style.RESET_ALL}")
                        else:
                            print(f"\n{Fore.RED}✗ Erro na sincronização da tabela '{table_name}'{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.YELLOW}Sincronização cancelada{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.RED}Opção inválida{Style.RESET_ALL}")
            except ValueError:
                print(f"\n{Fore.RED}Por favor, digite um número válido{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _show_history(self):
        """Mostrar histórico de sincronizações"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== HISTÓRICO DE SINCRONIZAÇÕES ==={Style.RESET_ALL}")
            
            # Opção de filtrar por tabela
            filter_table = input(f"\n{Fore.CYAN}Filtrar por tabela (deixe vazio para todas): {Style.RESET_ALL}").strip()
            filter_table = filter_table if filter_table else None
            
            history = self.config.get_sync_history(filter_table, 20)
            
            if not history:
                print(f"\n{Fore.YELLOW}Nenhum histórico encontrado{Style.RESET_ALL}")
            else:
                # Preparar dados para tabela
                history_data = []
                for record in history:
                    status = "Sucesso" if record['sync_status'] == 'success' else "Erro"
                    history_data.append([
                        record['table_name'],
                        record['sync_direction'],
                        str(record['records_affected'] or 0),
                        status,
                        record['started_at']
                    ])
                
                print(f"\n{Fore.CYAN}Últimos registros de sincronização:{Style.RESET_ALL}")
                print(tabulate(history_data, 
                             headers=["Tabela", "Direção", "Registros", "Status", "Data/Hora"],
                             tablefmt="grid"))
                
                # Mostrar erros se houver
                for record in history:
                    if record['error_message']:
                        print(f"\n{Fore.RED}Erro em {record['table_name']}: {record['error_message']}{Style.RESET_ALL}")
                
                print(f"\n{Fore.CYAN}Total: {len(history)} registros{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _toggle_table_menu(self):
        """Menu para ativar/desativar tabelas"""
        try:
            self.clear_screen()
            self.show_header()
            print(f"{Fore.GREEN}=== ATIVAR/DESATIVAR TABELAS ==={Style.RESET_ALL}")
            
            sync_tables = self.config.list_sync_tables()
            
            if not sync_tables:
                print(f"{Fore.YELLOW}Nenhuma tabela configurada para sincronização{Style.RESET_ALL}")
                input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
                return
            
            # Mostrar tabelas configuradas
            table_data = []
            for i, table in enumerate(sync_tables, 1):
                status = "Ativa" if table['active'] else "Inativa"
                table_data.append([str(i), table['table_name'], status])
            
            print(f"\n{Fore.CYAN}Tabelas configuradas:{Style.RESET_ALL}")
            print(tabulate(table_data, headers=["#", "Tabela", "Status"], 
                          tablefmt="grid", colalign=("center", "left", "center")))
            
            choice = input(f"\n{Fore.CYAN}Escolha a tabela para alterar status (1-{len(sync_tables)}): {Style.RESET_ALL}").strip()
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(sync_tables):
                    table_name = sync_tables[index]['table_name']
                    current_status = "ativa" if sync_tables[index]['active'] else "inativa"
                    new_status = "inativa" if sync_tables[index]['active'] else "ativa"
                    
                    confirm = input(f"\n{Fore.YELLOW}Tabela '{table_name}' está {current_status}. Alterar para {new_status}? (s/N): {Style.RESET_ALL}").strip().lower()
                    if confirm == 's':
                        if self.config.toggle_table_status(table_name):
                            print(f"\n{Fore.GREEN}✓ Status da tabela '{table_name}' alterado com sucesso!{Style.RESET_ALL}")
                        else:
                            print(f"\n{Fore.RED}✗ Erro ao alterar status da tabela{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.YELLOW}Operação cancelada{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.RED}Opção inválida{Style.RESET_ALL}")
            except ValueError:
                print(f"\n{Fore.RED}Por favor, digite um número válido{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"\n{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
    
    def _check_connections(self):
        """Verificar se as conexões estão configuradas"""
        source_conn = self.connection_manager.get_connection_by_type('source')
        target_conn = self.connection_manager.get_connection_by_type('target')
        
        if not source_conn or not target_conn:
            print(f"\n{Fore.RED}✗ Conexões não configuradas. Configure as conexões primeiro.{Style.RESET_ALL}")
            input(f"\n{Fore.CYAN}Pressione Enter para continuar...{Style.RESET_ALL}")
            return False
        
        return True
