#import logging
import os
import sys
from threading import Thread
from LibTaskbarClass import TaskBarIcon
from LibFrameClass import MyFrame
from LibEventClass import Event as MyEvent
from LibZabbixSender import ZabbixSender_
from LibFileLogger import FileLogger_
from LibFileOperations import FileOperations_
from watchdog.observers import Observer
import wx.adv
import wx

'''Criando variaveis utilizadas pelo sistema'''     
status = {                              # Evita que multiplos eventos ocorram ao mesmo tempo, causando falhas
        'sincronizando' : False,
        'evento_acontecendo' : False,
        'updating_logs' : False
    }
zabbix_metric = [0]                      #Variavel que carrega as metricas do zabbix

"""Criando objeto de adição de registros de log"""
logger_ = FileLogger_(pasta_de_logs='logs')

#'''Inicializando sistema de logging..'''
#logging.basicConfig(level=logging.INFO,
#                    format='%(asctime)s - %(message)s',
#                    datefmt='%Y-%m-%d %H:%M:%S') 

'''Carregando informações do diretório raiz do projeto'''
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

'''Carregando configurações...'''
if os.path.isfile('config.json'):
    configs = FileOperations_.read_json_from_file(None, "config.json")
else:
    logger_.adiciona_linha_log(f" Configuration file 'Config.json' was not found.")
    raise FileNotFoundError(f" Configuration file 'config.json' was not found.")

"""Criando instancias de envio de metricas para o zabbix"""
try:
    for instance in configs['zabbix_instances'].keys():
        ZabbixSender_(
            metric_interval= configs['zabbix_instances'][instance]['send_metrics_interval'], 
            hostname= configs['zabbix_instances'][instance]['hostname'], 
            key= configs['zabbix_key'], 
            server_ip= configs['zabbix_instances'][instance]['server_ip'],
            port= configs['zabbix_instances'][instance]['port'],
            idx= 0,
            metric= zabbix_metric
        )
except Exception as Err:
    logger_.adiciona_linha_log(f"Erro: {Err} - Configuration file 'config.json' can be wrong at Zabbix description.")
  
"""Inicializando a interface gráfica"""
try:
    app = wx.App()                                                                                      # Criação da aplicação wxpython
    frame = MyFrame(status=status, logger_=logger_, zabbix_metric=zabbix_metric, configs=configs)       # Criação da janela principal d aplicativo
    TaskBarIcon(frame, configs)                                                                     # Criação do ícone de bandeja
except Exception as Err:
    logger_.adiciona_linha_log(f"Erro: {Err} - Erro ao criar a interface gráfica da aplicação wxpython.")
    
"""Criando objeto de operacoes com arquivos"""
operations_ = FileOperations_(configs, frame, logger_)

"""Criando sistema de monitoração de alterações em diretórios"""                    
try:
    event_handler = MyEvent(mylogger=logger_, configs=configs, fileoperations=operations_)
    observer = Observer() 
except Exception as Err:
    logger_.adiciona_linha_log(f"Erro: {Err} - Erro ao criar estrutura de eventhandler and observer.")

def main():
    try:
        """Cadastro de itens no observer que monitora mudanças nos diretórios"""
        for item in configs['folders_to_sync']:
            observed_folder = configs['folders_to_sync'][item]['origem']         # lista com o diretorio monitorado e o diretório espelho 
            if os.path.isdir(observed_folder):
                observer.schedule(event_handler, observed_folder, recursive=False)   # criação do mecanismo de monitoramento                
            else:
                raise FileNotFoundError(f"{observed_folder} was not found or is a file")
        
        """Inicialização do serviço de observação de diretórios"""
        observer.start() 

        """Start threading de sincronismo de arquivos"""
        u = Thread(target=operations_.syncs_thread, args=[], daemon=True)   # Rotina que sincroniza todos os diretórios em intervalos regulares
        u.start()
        
        """Start threading de sincronismo de arquivos"""
        frame.update_logs()                 # Adiciona as linhas ao painel de logs quando o programa é recém aberto
        
        """Loop principal da execução da interface gráfica"""
        app.MainLoop()

    except Exception as Err:
        logger_.adiciona_linha_log(f'Erro em Main observer start: {sys._getframe().f_code.co_name}, Descrição: {Err}')
        frame.set_error_led()

if __name__ == "__main__":
    main()

