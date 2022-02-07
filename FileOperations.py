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
        assert isinstance(self.frame, MyFrame)      # verifica erros na passagem de argumentos e permite o uso do recurso autocompletar
        assert isinstance(self.logger_, FileLogger_)

        time_begin = round(time.time())
        retorna_erro = False
        
        in_file = None
        source_size1 = os.path.getsize( str(filepath_source) )
        source_size2 = os.path.getsize( str(filepath_source) )

        while in_file == None or source_size1 != source_size2:
            source_size1 = os.path.getsize( str(filepath_source) )
            time.sleep(0.02)
            source_size2 = os.path.getsize( str(filepath_source) )
            
            try:
                in_file = open(filepath_source, "rb") # opening for [r]eading as [b]inary
                time.sleep(0.01)
                in_file.close()            
            except:
                pass
            
            if (round(time.time()) > ( time_begin + 120) ):
                self.logger_.adiciona_linha_log("Arquivo protegido contra gravacao por mais de 120 segundos, não permitindo a cópia.")
                retorna_erro = True
                break
        return retorna_erro
   


    def filetree(self, source, dest, sync_name):     
        assert isinstance(self.frame, MyFrame)      # verifica erros na passagem de argumentos e permite o uso do recurso autocompletar
        assert isinstance(self.logger_, FileLogger_)

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

            debug = 'destination.pop'  
            for item in files_to_remove:
                files_destination_md5.pop(item)

            debug = 'copy files'
            thistime=round(time.time())
            for file in files_source_md5:
                path_source = os.path.join(source, file)
                path_dest = os.path.join(dest, file)
                if file not in files_destination_md5:
                    
                    if self.aguarda_liberar_arquivo(path_source):
                        return 1
                    
                    shutil.copy2(path_source, path_dest)                
                    self.logger_.adiciona_linha_log("Copiado: " + str(path_source) + "[" + str(os.path.getsize( str(path_source) )) + "]" + " to " + str(path_dest) + "[" + str(os.path.getsize(str(path_dest) )) + "]")
                else:            
                    if files_source_md5[file] != files_destination_md5[file]:
                        
                        if self.aguarda_liberar_arquivo(path_source):
                            return 1
                        
                        shutil.copy2(path_source, path_dest)
                        self.logger_.adiciona_linha_log("Sobrescrito: " + str(path_source) + "[" + str(os.path.getsize( str(path_source) )) + "]" + " to " + str(path_dest) + "[" + str(os.path.getsize( str(path_dest) )) + "]")
                if (round(time.time()) > ( thistime + 120) ):
                    return 0   
            return 0

        except Exception as err:
            assert isinstance(self.frame, MyFrame)      # verifica erros na passagem de argumentos e permite o uso do recurso autocompletar
            assert isinstance(self.frame.zabbix_instance, ZabbixSender_)
            self.frame.zabbix_instance.metric[self.frame.zabbix_instance.idx] = str(source) 
            self.logger_.adiciona_linha_log(f' {err} {debug}')
            print  (f' {err} {debug}')
            return 1

    def sync_all_folders(self):
        assert isinstance(self.frame, MyFrame)
        assert isinstance(self.logger_, FileLogger_)
        assert isinstance(self.frame.zabbix_instance, ZabbixSender_)

        try:
            self.frame.update_logs()
            error_counter = 0
            for item in self.configs['SYNC_FOLDERS']:
                time.sleep(0.1)
                path = (self.configs['SYNC_FOLDERS'][item]).split(', ')
                error_counter += self.filetree(path[0], path[1], item)
                time.sleep(0.1)
            if error_counter == 0:
                self.frame.zabbix_instance.metric[self.frame.zabbix_instance.idx] = 0
                self.frame.clear_error_led()
            else:
                self.frame.zabbix_instance.metric[self.frame.zabbix_instance.idx] = 1
                self.frame.set_error_led()

        except Exception as err:
            self.logger_.adiciona_linha_log("Falha durante execução da função sync_all_folders - "+str(err))
            self.frame.set_error_led()


    def syncs_thread(self):
        assert isinstance(self.frame, MyFrame)
        sleep_time = int(self.configs['SYNC_TIMES']['sync_with_no_events_time'])
        while sleep_time > 0:
            self.frame.set_sync_waiting_led()
            self.frame.status['sincronizando'] = True
            if self.frame.status['evento_acontecendo']:
                self.frame.status['sincronizando'] = False
                time.sleep(1)
                continue
            self.frame.set_sync_in_progress_led()
            self.sync_all_folders()                                 #realiza rotina de sincronizar todos os diretorios
            self.frame.status['sincronizando'] = False
            self.frame.clear_sync_in_progress_led()
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

    def event_operations(self, filepath_source, path_dest, sync_name, event):
        assert isinstance(self.frame, MyFrame)
        assert isinstance(self.logger_, FileLogger_)
        assert isinstance(self.frame.zabbix_instance, ZabbixSender_)

        self.frame.status['evento_acontecendo'] = True
        while self.frame.status['sincronizando'] == True:
            self.frame.set_event_waiting_led()
            time.sleep(0.1) 
        self.frame.set_event_in_progress_led()
        try: 
            sync_ext = configs['SYNC_EXTENSIONS'][sync_name].lower().split(", ")
        except:
            sync_ext = []
        try:
            filename = self.getfilename(filepath_source).lower()
            filepath_dest = os.path.join(path_dest, filename)
            if os.path.isfile(filepath_source) or os.path.isfile(filepath_dest):
                if (os.path.splitext(filename)[1][1:].lower() in sync_ext) or (len(sync_ext) == 0):    
                    if not os.path.exists(filepath_source):
                        try:
                            os.remove(filepath_dest)
                            self.logger_.adiciona_linha_log("Removido: " + str(filepath_dest))
                        except Exception as err:
                            self.logger_.adiciona_linha_log(str(err) + "Erro ao remover arquivo. " + str(filepath_dest))
                            self.frame.set_error_led()       
                    elif not os.path.exists(filepath_dest):
                        self.aguarda_liberar_arquivo(filepath_source)
                        shutil.copy2(filepath_source, filepath_dest)
                        origem_size = os.path.getsize( str(filepath_source) )
                        destino_size = os.path.getsize( str(filepath_dest) )
                        self.logger_.adiciona_linha_log("Copiado: " + str(filepath_source) + "[" + str(origem_size) + "]" + " to " + str(filepath_dest) + "[" + str(destino_size) + "]")  
                        if (origem_size != destino_size):
                            os.remove(filepath_dest)
                            self.logger_.adiciona_linha_log('Cópia corrompida. Será copiado novamente no próximo sync.' + str(filepath_source))
                            self.frame.set_error_led()
                    else:
                        source_mtime = os.stat(filepath_source).st_mtime
                        dest_mtime = os.stat(filepath_dest).st_mtime
                        if source_mtime != dest_mtime:
                            self.aguarda_liberar_arquivo(filepath_source)
                            shutil.copy2(filepath_source, filepath_dest)
                            origem_size = os.path.getsize( str(filepath_source) )
                            destino_size = os.path.getsize( str(filepath_dest) )
                            self.logger_.adiciona_linha_log("Sobrescrito: " + str(filepath_source) + "[" + str(origem_size) + "]" + " to " + str(filepath_dest) + "[" + str(destino_size) + "]")
                            if (origem_size != destino_size):
                                os.remove(filepath_dest)
                                self.logger_.adiciona_linha_log('Cópia corrompida. Será copiado novamente no próximo sync' + str(filepath_source)) 
                                self.frame.set_error_led()
            self.frame.clear_event_in_progress_led()
        except Exception as Err:
            self.logger_.adiciona_linha_log(str(Err)) 
            self.frame.zabbix_instance.metric = 1
        self.frame.status['evento_acontecendo'] = False


    def getfilename(self, filepath):
        assert isinstance(self.logger_, FileLogger_)
        try:
            pathlist = filepath.split('\\')
            filename = (pathlist[len(pathlist)-1]).lower()
            return (filename)
        except Exception as Err:
            pass
            self.logger_.adiciona_linha_log(str(Err)+'Getfilename')


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
    frame = MyFrame(status=status, logger_=logger_, zabbix_instance= zsender, configs=configs)       # Janela principal

    fileoperations_ = FileOperations_(configs, frame, logger_)
    fileoperations_.start_sync_thread()
    while 1:
        pass
        time.sleep(1)
