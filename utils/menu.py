#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de menus da aplicação
"""

import os
from colorama import Fore, Style
from tabulate import tabulate

class Menu:
    def __init__(self, logger):
        """Inicializar sistema de menus"""
        self.logger = logger
    
    def clear_screen(self):
        """Limpar a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Mostrar cabeçalho da aplicação"""
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}{'  MySQL/MariaDB STRUCTURE REPLICATOR':^70}")
        print(f"{Fore.CYAN}{'  Replicação Segura de Estrutura de Banco de Dados':^70}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    def show_main_menu(self):
        """Mostrar menu principal"""
        self.clear_screen()
        self.show_header()
        
        print(f"{Fore.GREEN}=== MENU PRINCIPAL ==={Style.RESET_ALL}")
        
        options = [
            ["1", "Configurar Conexões", "Gerenciar conexões de banco de dados"],
            ["2", "Testar Conexões", "Verificar conectividade com os bancos"],
            ["3", "Diagnosticar Sistema", "Diagnóstico completo de conexões"],
            ["4", "Analisar Estruturas", "Comparar estruturas dos bancos"],
            ["5", "Replicar Estrutura", "Executar replicação da estrutura"],
            ["6", "Sincronizar Dados", "Sincronizar dados entre ambientes"],
            ["7", "Visualizar Logs", "Ver histórico de operações"],
            ["8", "Gerenciar Backups", "Criar e gerenciar backups"],
            ["0", "Sair", "Encerrar aplicação"]
        ]
        
        print(tabulate(options, headers=["Opção", "Ação", "Descrição"], 
                      tablefmt="grid", colalign=("center", "left", "left")))
        
        choice = input(f"\n{Fore.CYAN}Escolha uma opção (0-8): {Style.RESET_ALL}").strip()
        return choice
    
    def show_connection_menu(self):
        """Mostrar menu de conexões"""
        self.clear_screen()
        self.show_header()
        
        print(f"{Fore.GREEN}=== CONFIGURAÇÃO DE CONEXÕES ==={Style.RESET_ALL}")
        
        options = [
            ["1", "Configurar Banco de Origem (Teste)", "Banco onde estão as novas estruturas"],
            ["2", "Configurar Banco de Destino (Produção)", "Banco que receberá as alterações"],
            ["3", "Listar Conexões", "Ver conexões configuradas"],
            ["4", "Remover Conexão", "Deletar conexão existente"],
            ["0", "Voltar", "Retornar ao menu principal"]
        ]
        
        print(tabulate(options, headers=["Opção", "Ação", "Descrição"], 
                      tablefmt="grid", colalign=("center", "left", "left")))
        
        choice = input(f"\n{Fore.CYAN}Escolha uma opção (0-4): {Style.RESET_ALL}").strip()
        return choice
    
    def show_backup_menu(self):
        """Mostrar menu de backups"""
        self.clear_screen()
        self.show_header()
        
        print(f"{Fore.GREEN}=== GERENCIAMENTO DE BACKUPS ==={Style.RESET_ALL}")
        
        options = [
            ["1", "Criar Backup Manual", "Fazer backup de um banco específico"],
            ["2", "Listar Backups", "Ver backups disponíveis"],
            ["3", "Restaurar Backup", "Restaurar backup (função informativa)"],
            ["0", "Voltar", "Retornar ao menu principal"]
        ]
        
        print(tabulate(options, headers=["Opção", "Ação", "Descrição"], 
                      tablefmt="grid", colalign=("center", "left", "left")))
        
        choice = input(f"\n{Fore.CYAN}Escolha uma opção (0-3): {Style.RESET_ALL}").strip()
        return choice
    
    def get_connection_details(self, connection_type):
        """Obter detalhes da conexão do usuário"""
        self.clear_screen()
        self.show_header()
        
        type_name = "ORIGEM (Teste)" if connection_type == "source" else "DESTINO (Produção)"
        
        print(f"{Fore.CYAN}=== CONFIGURAÇÃO DE CONEXÃO {type_name} ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Digite os dados da conexão:{Style.RESET_ALL}\n")
        
        details = {}
        
        # Nome da conexão
        details['name'] = input(f"{Fore.WHITE}Nome da conexão: {Style.RESET_ALL}").strip()
        if not details['name']:
            details['name'] = f"Conexão {type_name}"
        
        # Host
        details['host'] = input(f"{Fore.WHITE}Host/IP do servidor: {Style.RESET_ALL}").strip()
        if not details['host']:
            details['host'] = "localhost"
        
        # Porta
        port_input = input(f"{Fore.WHITE}Porta (padrão 3306): {Style.RESET_ALL}").strip()
        try:
            details['port'] = int(port_input) if port_input else 3306
        except ValueError:
            details['port'] = 3306
        
        # Usuário
        details['username'] = input(f"{Fore.WHITE}Usuário: {Style.RESET_ALL}").strip()
        
        # Senha
        import getpass
        details['password'] = getpass.getpass(f"{Fore.WHITE}Senha: {Style.RESET_ALL}")
        
        # Nome do banco
        details['database'] = input(f"{Fore.WHITE}Nome do banco de dados: {Style.RESET_ALL}").strip()
        
        # Tipo da conexão
        details['type'] = connection_type
        
        # Confirmar dados
        print(f"\n{Fore.CYAN}=== CONFIRMAÇÃO DOS DADOS ==={Style.RESET_ALL}")
        confirmation_data = [
            ["Nome", details['name']],
            ["Tipo", type_name],
            ["Host", details['host']],
            ["Porta", str(details['port'])],
            ["Usuário", details['username']],
            ["Senha", "*" * len(details['password'])],
            ["Banco", details['database']]
        ]
        
        print(tabulate(confirmation_data, headers=["Campo", "Valor"], 
                      tablefmt="grid", colalign=("left", "left")))
        
        confirm = input(f"\n{Fore.CYAN}Confirma os dados? (s/N): {Style.RESET_ALL}").strip().lower()
        
        if confirm == 's':
            return details
        else:
            print(f"{Fore.YELLOW}Configuração cancelada.{Style.RESET_ALL}")
            return None
    
    def display_connections(self, connections):
        """Exibir lista de conexões"""
        self.clear_screen()
        self.show_header()
        
        if not connections:
            print(f"{Fore.YELLOW}Nenhuma conexão configurada.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}=== CONEXÕES CONFIGURADAS ==={Style.RESET_ALL}")
        
        data = []
        for conn in connections:
            conn_type = "ORIGEM (Teste)" if conn['type'] == 'source' else "DESTINO (Produção)"
            data.append([
                conn['id'],
                conn['name'],
                conn_type,
                f"{conn['host']}:{conn['port']}",
                conn['username'],
                conn['database'],
                conn['updated_at'][:19] if conn['updated_at'] else "N/A"
            ])
        
        headers = ["ID", "Nome", "Tipo", "Servidor", "Usuário", "Banco", "Atualizada em"]
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def select_connection(self, connections, prompt="Selecione uma conexão"):
        """Permitir seleção de uma conexão"""
        if not connections:
            print(f"{Fore.YELLOW}Nenhuma conexão disponível.{Style.RESET_ALL}")
            return None
        
        self.display_connections(connections)
        
        try:
            choice = int(input(f"\n{Fore.CYAN}{prompt} (ID): {Style.RESET_ALL}"))
            
            for conn in connections:
                if conn['id'] == choice:
                    return conn
            
            print(f"{Fore.RED}ID de conexão inválido.{Style.RESET_ALL}")
            return None
        
        except ValueError:
            print(f"{Fore.RED}Entrada inválida. Digite apenas números.{Style.RESET_ALL}")
            return None
    
    def confirm_operation(self, operation_name, details=None):
        """Confirmar operação crítica"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"{Fore.YELLOW}CONFIRMAÇÃO DE OPERAÇÃO: {operation_name}")
        print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        
        if details:
            for detail in details:
                print(f"{Fore.WHITE}• {detail}{Style.RESET_ALL}")
        
        print(f"\n{Fore.RED}ATENÇÃO: Esta operação pode modificar a estrutura do banco de dados!")
        print(f"{Fore.RED}Um backup será criado automaticamente antes de qualquer alteração.{Style.RESET_ALL}")
        
        confirm = input(f"\n{Fore.CYAN}Deseja continuar? Digite 'CONFIRMO' para prosseguir: {Style.RESET_ALL}").strip()
        
        return confirm.upper() == 'CONFIRMO'
    
    def show_progress(self, current, total, description="Processando"):
        """Mostrar barra de progresso simples"""
        percentage = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r{Fore.CYAN}{description}: |{bar}| {percentage:.1f}% ({current}/{total}){Style.RESET_ALL}", end='')
        
        if current == total:
            print()  # Nova linha quando completo
