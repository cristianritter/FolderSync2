import logging
#import parse_config
import os
import sys

from LibTaskbarClass import TaskBarIcon

from LibFrameClass import MyFrame
from LibEventClass import Event as MyEvent
from LibZabbixSender import ZabbixSender_
from LibFileLogger import FileLogger_
from LibFileOperations import FileOperations_

from watchdog.observers import Observer
import wx.adv
import wx

try:    
    '''Carregando informações do diretório raiz do projeto'''
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    

    '''Carregando configurações...'''
#    configuration = parse_config.ConfPacket()
#    configs: str = configuration.load_config('SYNC_FOLDERS, SYNC_TIMES, SYNC_EXTENSIONS, ZABBIX, SYNC_NAME')

    configs = FileOperations_.read_json_from_file(None, "config.json")


    '''Variavel de status do sistema'''     # Evita que multiplos eventos ocorram ao mesmo tempo, causando falhas
    status = {
            'sincronizando' : False,
            'evento_acontecendo' : False,
            'updating_logs' : False
        }


    """Criando instancias de envio de metricas para o zabbix"""
    zabbix_metric = [0]
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

    """Criando objeto de adição de registros de log"""
    logger_ = FileLogger_(pasta_de_logs='logs')

    
    """Inicializando a interface gráfica"""
    app = wx.App()  
    frame = MyFrame(status=status, logger_=logger_, zabbix_metric=zabbix_metric, configs=configs)       # Janela principal
    TaskBarIcon(frame, configs)      # Icone de bandeja

    """Criando objeto de operacoes com arquivos"""
    operations_ = FileOperations_(configs, frame, logger_)

    '''Inicializando sistema de logging..'''
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S') 
    
    event_handler = MyEvent(mylogger=logger_, configs=configs, fileoperations=operations_)


    observer = Observer() 
    
    exit()
                
    if __name__ == "__main__":
        try:
            for item in configs['SYNC_FOLDERS']:
                monitored_folder = (configs['SYNC_FOLDERS'][item]).split(', ')           # lista com o diretorio monitorado e o diretório espelho 
                observer.schedule(event_handler, monitored_folder[0], recursive=False)   # criação do mecanismo de monitoramento   
            
            observer.start() 
            
            """Start threading de sincronismo de arquivos"""
            operations_.start_timesync_thread()

            """Start threading de envio de metricas para o zabbix"""
            #zsender.start_zabbix_thread()

            frame.update_logs()

            app.MainLoop()

        except Exception as Err:
            logger_.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            frame.set_error_led()
      
except Exception as Err:
    logger_.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')


