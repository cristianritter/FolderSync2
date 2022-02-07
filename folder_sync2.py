import logging
import parse_config
import os

from taskbar_class import TaskBarIcon
from frame_class import MyFrame
from event_class import Event as MyEvent

from ZabbixSender import ZabbixSender_
from FileLogger import FileLogger

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

    '''Organizando parametros do zabbix'''
    zabbix_metric = []

    zabbix_param = {
        'HOSTNAME' : configs['ZABBIX']['hostname'],
        'SERVER' : configs['ZABBIX']['zabbix_server'],
        'PORT' : int(configs['ZABBIX']['port']),
        'KEY' : configs['ZABBIX']['key'],
        'METRICS_INTERVAL' : int(configs['ZABBIX']['send_metrics_interval'])
    }

    status = {
        'sincronizando' : False,
        'evento_acontecendo' : False,
        'updating_logs' : False
    }

    """Criando objeto de envio de metricas para o zabbix"""
    zsender = ZabbixSender_(
        metric_interval= zabbix_param['METRICS_INTERVAL'], 
        hostname= zabbix_param['HOSTNAME'], 
        key= zabbix_param['KEY'], 
        server= zabbix_param['SERVER'],
        port= zabbix_param['PORT'],
        idx= 0,
        status= zabbix_metric
    )

    """Criando objeto de adição de registros de log"""
    logger_ = FileLogger(pasta_de_logs='logs')

    """Inicializando a interface gráfica"""
    app = wx.App()  
    frame = MyFrame(status=status, logger_=logger_, zabbix_metric=zabbix_metric)       # Janela principal
    TaskBarIcon(frame)      # Icone de bandeja

    '''Inicializando sistema de logging..'''
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S') 
    
    event_handler = MyEvent()

    observer = Observer() 
    
    
                
    if __name__ == "__main__":

        for item in configs['SYNC_FOLDERS']:
            try:
                pass
                host = (configs['SYNC_FOLDERS'][item]).split(', ')
                observer.schedule(event_handler, host[0], recursive=False)
            except Exception as err:
                print('threds ' + str(err))
                logger_.adiciona_linha_log(str(err)+host[0])
                frame.set_error_led()

        observer.start() 
        
        try:      

            t = Thread(target=frame.syncs_thread, daemon=True)

            zsender.start_zabbix_thread()
            t.start()
            frame.update_logs()

            app.MainLoop()

        except Exception as Err:
            logger_.adiciona_linha_log('trheads' + str(Err))
            frame.set_error_led()
      
except Exception as ERR:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    print('main'+ str(ERR))
    dire = os.path.join(ROOT_DIR, 'ERRO.TXT')
    f = open(dire, "a")
    f.write(str(ERR))
    f.close()
   


