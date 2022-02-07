import time
import shutil
import os
from threading import Thread
from ZabbixSender import ZabbixSender_
from FileLogger import FileLogger_
from frame_class import MyFrame


class FileOperations_():
    def __init__(self, config_dict, frame_inst, logger_inst) -> None:
        self.configs = config_dict
        self.frame = frame_inst
        self.logger_ = logger_inst
        assert isinstance(self.frame, MyFrame)      # verifica erros na passagem de argumentos e permite o uso do recurso autocompletar
        assert isinstance(self.logger_, FileLogger_)
   
    def aguarda_liberar_arquivo(self, filepath_source):
        thistime2=round(time.time())
        in_file = None
        source_size1 = 0
        source_size2 = -1
        while in_file == None or source_size1 != source_size2:
            source_size1 = os.path.getsize( str(filepath_source) )
            time.sleep(0.02)
            source_size2 = os.path.getsize( str(filepath_source) )
            try:
                in_file = open(filepath_source, "rb") # opening for [r]eading as [b]inary
            except:
                pass
            if (round(time.time()) > ( thistime2 + 120) ):
                self.logger_.adiciona_linha_log("Arquivo protegido contra gravacao por mais de 120 segundos, não permitindo a cópia.")
                self.frame.set_error_led()
                break
        try:
            in_file.close()            
        except:
            pass


    def filetree(self, source, dest, sync_name):     
        files_destination_md5=dict()
        files_source_md5=dict()
        try: 
            sync_ext = self.configs['SYNC_EXTENSIONS'][sync_name].lower().split(", ")
        except:
            sync_ext = []

        try:
            debug = 'scan dest'
            for e in os.scandir(dest):
                if e.is_file():
                    if (not os.path.splitext(e.name)[1][1:].lower() in sync_ext) & (len(sync_ext) > 0):
                        continue
                    files_destination_md5[e.name.lower()]=e.stat().st_mtime
                
            debug = 'scan source'
            for e in os.scandir(source):
                if e.is_file():
                    if (not os.path.splitext(e.name)[1][1:].lower() in sync_ext) & (len(sync_ext) > 0):
                        continue
                    files_source_md5[e.name.lower()]=e.stat().st_mtime
                
            files_to_remove=[]

            debug = 'remove files'
            for file in files_destination_md5:
                path_dest = os.path.join(dest, file)
                if file not in files_source_md5:
                    try:
                        os.remove(path_dest)
                        self.logger_.adiciona_linha_log("Removido: " + str(path_dest))
                        files_to_remove.append(file)
                    except Exception as ERR:
                        self.logger_.adiciona_linha_log("Erro ao remover arquivo." + str(ERR))
                        self.frame.set_error_led()

            debug = 'destination.pop'  
            for item in files_to_remove:
                files_destination_md5.pop(item)

            debug = 'copy files'
            thistime=round(time.time())
            for file in files_source_md5:
                path_source = os.path.join(source, file)
                path_dest = os.path.join(dest, file)
                if file not in files_destination_md5:
                    self.aguarda_liberar_arquivo(path_source) #testar
                    shutil.copy2(path_source, path_dest)                
                    self.logger_.adiciona_linha_log("Copiado: " + str(path_source) + "[" + str(os.path.getsize( str(path_source) )) + "]" + " to " + str(path_dest) + "[" + str(os.path.getsize(str(path_dest) )) + "]")
                else:            
                    if files_source_md5[file] != files_destination_md5[file]:
                        self.aguarda_liberar_arquivo(path_source) #testar
                        shutil.copy2(path_source, path_dest)
                        self.logger_.adiciona_linha_log("Sobrescrito: " + str(path_source) + "[" + str(os.path.getsize( str(path_source) )) + "]" + " to " + str(path_dest) + "[" + str(os.path.getsize( str(path_dest) )) + "]")
                if (round(time.time()) > ( thistime + 120) ):
                    return 0   
            return 0

        except Exception as err:
            assert isinstance(self.frame, MyFrame)      # verifica erros na passagem de argumentos e permite o uso do recurso autocompletar
            assert isinstance(self.frame.zabbix_param, ZabbixSender_)
            self.frame.zabbix_param.metric[self.frame.zabbix_param.idx] = str(source) 
            self.logger_.adiciona_linha_log(str(err)+debug)
            print  ('erro in filetree')
            return 1


    def sync_all_folders(self):
        try:
            self.frame.update_logs()
            error_counter = 0
            for item in self.configs['SYNC_FOLDERS']:
                time.sleep(0.1)
                path = (self.configs['SYNC_FOLDERS'][item]).split(', ')
                error_counter += self.filetree(path[0], path[1], item)
                time.sleep(0.1)
            if error_counter == 0:
                self.frame.zabbix_param.metric[self.frame.zabbix_param.idx] = 0
        except Exception as err:
            self.logger_.adiciona_linha_log("Falha durante execução da função sync_all_folders - "+str(err))
            self.frame.set_error_led()


    def syncs_thread(self):
        assert isinstance(self.frame, MyFrame)
        sleep_time = int(self.configs['SYNC_TIMES']['sync_with_no_events_time'])
        while sleep_time > 0:
            self.frame.set_sync_waiting_led()
            self.frame.Refresh()
            self.frame.status['sincronizando'] = True
            if self.frame.status['evento_acontecendo']:
                self.frame.status['sincronizando'] = False
                time.sleep(1)
                continue
            self.frame.set_sync_in_progress_led()
            self.frame.Refresh()
            self.sync_all_folders()
            self.frame.status['sincronizando'] = False
            self.frame.clear_sync_in_progress_led()
            self.frame.Refresh()
            time.sleep(sleep_time)

    def start_sync_thread(self):
        """
        Método que inicia um thread de envio de metricas para o zabbix
        """
        try:
            u = Thread(target=self.syncs_thread, args=[], daemon=True)
            u.start()
        except Exception as Err:
            print(f'Erro: {Err}')

if __name__ == '__main__':
    import parse_config
    import wx

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


    """Criando objeto de adição de registros de log"""
    logger_ = FileLogger_(pasta_de_logs='logs')

    '''Organizando parametros do zabbix'''
    zabbix_param = {
        'HOSTNAME' : configs['ZABBIX']['hostname'],
        'SERVER' : configs['ZABBIX']['zabbix_server'],
        'PORT' : int(configs['ZABBIX']['port']),
        'KEY' : configs['ZABBIX']['key'],
        'METRICS_INTERVAL' : int(configs['ZABBIX']['send_metrics_interval'])
    }

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

    fileoperations_ = FileOperations_(configs, frame, logger_)
    fileoperations_.start_sync_thread()
    while 1:
        pass
        time.sleep(1)
