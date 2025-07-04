#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de logging da aplicação
"""

import os
import logging
import datetime
from colorama import Fore, Style

class Logger:
    def __init__(self):
        """Inicializar sistema de logging"""
        self.logs_dir = "logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Configurar logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configurar sistema de logging"""
        # Nome do arquivo de log baseado na data
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.logs_dir, f"replicator_{today}.log")
        
        # Configurar formato
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Configurar logger
        logging.basicConfig(
            level=logging.DEBUG,  # Mudado de INFO para DEBUG
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('DBReplicator')
    
    def info(self, message):
        """Log de informação"""
        self.logger.info(message)
        print(f"{Fore.CYAN}INFO: {message}{Style.RESET_ALL}")
    
    def success(self, message):
        """Log de sucesso"""
        self.logger.info(f"SUCCESS: {message}")
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def warning(self, message):
        """Log de aviso"""
        self.logger.warning(message)
        print(f"{Fore.YELLOW}⚠ WARNING: {message}{Style.RESET_ALL}")
    
    def error(self, message):
        """Log de erro"""
        self.logger.error(message)
        print(f"{Fore.RED}✗ ERROR: {message}{Style.RESET_ALL}")
    
    def debug(self, message):
        """Log de debug"""
        self.logger.debug(message)
    
    def operation_start(self, operation):
        """Log de início de operação"""
        msg = f"Iniciando operação: {operation}"
        self.logger.info(msg)
        print(f"\n{Fore.BLUE}{'='*50}")
        print(f"{Fore.BLUE}{msg}")
        print(f"{Fore.BLUE}{'='*50}{Style.RESET_ALL}")
    
    def operation_end(self, operation, success=True):
        """Log de fim de operação"""
        status = "CONCLUÍDA" if success else "FALHADA"
        msg = f"Operação {operation} - {status}"
        
        if success:
            self.logger.info(msg)
            print(f"{Fore.GREEN}{'='*50}")
            print(f"{Fore.GREEN}{msg}")
            print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}\n")
        else:
            self.logger.error(msg)
            print(f"{Fore.RED}{'='*50}")
            print(f"{Fore.RED}{msg}")
            print(f"{Fore.RED}{'='*50}{Style.RESET_ALL}\n")
    
    def step(self, step_number, total_steps, description):
        """Log de passo da operação"""
        msg = f"Passo {step_number}/{total_steps}: {description}"
        self.logger.info(msg)
        print(f"{Fore.CYAN}[{step_number}/{total_steps}] {description}{Style.RESET_ALL}")
    
    def display_recent_logs(self, lines=20):
        """Exibir logs recentes"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.logs_dir, f"replicator_{today}.log")
        
        if not os.path.exists(log_file):
            print(f"{Fore.YELLOW}Nenhum log encontrado para hoje.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}=== ÚLTIMAS {lines} ENTRADAS DE LOG ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}Arquivo: {log_file}{Style.RESET_ALL}\n")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if 'ERROR' in line:
                        print(f"{Fore.RED}{line}{Style.RESET_ALL}")
                    elif 'WARNING' in line:
                        print(f"{Fore.YELLOW}{line}{Style.RESET_ALL}")
                    elif 'SUCCESS' in line:
                        print(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.WHITE}{line}{Style.RESET_ALL}")
        
        except Exception as e:
            self.error(f"Erro ao ler arquivo de log: {e}")
    
    def get_log_files(self):
        """Obter lista de arquivos de log"""
        log_files = []
        if os.path.exists(self.logs_dir):
            for file in os.listdir(self.logs_dir):
                if file.startswith('replicator_') and file.endswith('.log'):
                    file_path = os.path.join(self.logs_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    log_files.append({
                        'name': file,
                        'path': file_path,
                        'size': file_size,
                        'modified': file_modified
                    })
        
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)
    
    def get_recent_operations(self, minutes=5):
        """Obter operações recentes dos logs"""
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.logs_dir, f"replicator_{today}.log")
            
            if not os.path.exists(log_file):
                return []
            
            cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
            recent_operations = []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Extrair timestamp da linha de log
                    try:
                        timestamp_str = line.split(' - ')[0]
                        log_time = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if log_time >= cutoff_time:
                            recent_operations.append(line)
                    except (ValueError, IndexError):
                        continue
            
            return recent_operations
            
        except Exception as e:
            self.error(f"Erro ao obter operações recentes: {str(e)}")
            return []
