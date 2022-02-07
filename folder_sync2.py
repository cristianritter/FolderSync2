import logging
import parse_config
import os

from taskbar_class import TaskBarIcon
from frame_class import MyFrame
from event_class import Event as MyEvent

from ZabbixSender import ZabbixSender_
from FileLogger import FileLogger_
from FileOperations import FileOperations_

from watchdog.observers import Observer
from threading import Thread
import wx.adv
import wx

try:    
    '''Carregando informações do diretório raiz do projeto'''
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    

    '''Carregando configurações...'''
    configuration = parse_config.ConfPacket()
    configs = configuration.load_config('SYNC_FOLDERS, SYNC_TIMES, SYNC_EXTENSIONS, ZABBIX, SYNC_NAME')


    '''Variavel de status do sistema'''
    status = {
            'sincronizando' : False,
            'evento_acontecendo' : False,
            'updating_logs' : False
        }


    '''Organizando parametros do zabbix'''
    zabbix_param = {
        'HOSTNAME' : configs['ZABBIX']['hostname'],
        'SERVER' : configs['ZABBIX']['zabbix_server'],
        'PORT' : int(configs['ZABBIX']['port']),
        'KEY' : configs['ZABBIX']['key'],
        'METRICS_INTERVAL' : int(configs['ZABBIX']['send_metrics_interval'])
    }


    """Criando objeto de adição de registros de log"""
    logger_ = FileLogger_(pasta_de_logs='logs')


    """Criando objeto de envio de metricas para o zabbix"""
    zsender = ZabbixSender_(
        metric_interval= zabbix_param['METRICS_INTERVAL'], 
        hostname= zabbix_param['HOSTNAME'], 
        key= zabbix_param['KEY'], 
        server= zabbix_param['SERVER'],
        port= zabbix_param['PORT'],
        idx= 0,
        metric= [0]
    )


    """Inicializando a interface gráfica"""
    app = wx.App()  
    frame = MyFrame(status=status, logger_=logger_, zabbix_param= zsender)       # Janela principal
    TaskBarIcon(frame)      # Icone de bandeja


    """Criando objeto de operacoes com arquivos"""
    operations_ = FileOperations_(configs, frame, logger_)


    '''Inicializando sistema de logging..'''
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S') 
    

    event_handler = MyEvent()


    observer = Observer() 
    
                
    if __name__ == "__main__":
        try:
            for item in configs['SYNC_FOLDERS']:
                monitored_folder = (configs['SYNC_FOLDERS'][item]).split(', ')           # lista com o diretorio monitorado e o diretório espelho 
                observer.schedule(event_handler, monitored_folder[0], recursive=False)   # criação do mecanismo de monitoramento   
            
            observer.start() 
            
            """Start threading de sincronismo de arquivos"""
            operations_.start_sync_thread()

            """Start threading de envio de metricas para o zabbix"""
            zsender.start_zabbix_thread()

            frame.update_logs()

            app.MainLoop()

        except Exception as Err:
            print('erro')
            logger_.adiciona_linha_log('trheads' + str(Err))
            frame.set_error_led()
      
except Exception as ERR:
    print('main'+ str(ERR))
    logger_.adiciona_linha_log(str(ERR)+'\n')


