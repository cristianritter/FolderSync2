import time
import shutil
import os
import sys
from threading import Thread
from LibZabbixSender import ZabbixSender_
from LibFileLogger import FileLogger_
from LibFrameClass import MyFrame
import json


class FileOperations_():
    def __init__(self, config_dict: dict, frame_inst: MyFrame, logger_inst: FileLogger_) -> bool:
        
        """Inicialização da classe"""
        
        self.configs = config_dict
        self.frame = frame_inst
        self.logger_ = logger_inst
    
    def read_json_from_file(self, filename):
        """     Carrega o conteúdo de um arquivo no formato Json para um dicionário"""
        try:
            """Le dados do arquivo"""
            with open(filename, 'r', encoding='utf-8') as infile:
                data = json.load(infile)
            return data
        except Exception as Err:
            print(Err, 'carregando aquivo')
            return 0

    def aguarda_liberar_arquivo(self, filepath_source):
   
        """Método que verifica se a criação do arquivo já foi finalizada antes de executar a cópia \n
        Retorna True se o arquivo estiver preso e não pode ser aberto por algum motivo desconhecido."""
   
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
                with open(filepath_source, "rb") as in_file: # opening for [r]eading as [b]inary
                    time.sleep(0.02)
            except:
                pass
            
            if (round(time.time()) > ( time_begin + 20) ):
                self.logger_.adiciona_linha_log("Arquivo protegido contra gravacao por mais de 20 segundos, não permitindo a cópia.")
                retorna_erro = True
                break
        return retorna_erro
   

    def filetree(self, source, dest, sync_name):  

        files_destination_md5=dict()
        files_source_md5=dict()

        try: 
            sync_ext : list = self.configs['folders_to_sync'][sync_name]['sync_extensions']
        except:
            sync_ext = []

        try:
            debug = 'scan dest'
            for e in os.scandir(dest):
                if e.is_file():
                    if (not os.path.splitext(e.name)[1][1:].lower() in sync_ext.lower()) & (len(sync_ext) > 0):
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
                    except Exception as Err:
                        self.logger_.adiciona_linha_log("Erro ao remover arquivo." + str(Err))

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
            self.frame.zabbix_instance.metric[self.frame.zabbix_instance.idx] = str(source) 
            self.logger_.adiciona_linha_log(f' {err} {debug}')
            print  (f' {err} {debug}')
            return 1

    def sync_all_folders(self):
  
        try:
            self.frame.update_logs()
            error_counter = 0
            for item in self.configs['folders_to_sync']:
                time.sleep(0.1)
                path = [0,0]
                path[0] = self.configs['folders_to_sync'][item]['origem']  #diretorio de origem
                path[1] = self.configs['folders_to_sync'][item]['destino'] # diretorio de destino
                error_counter += self.filetree(path[0], path[1], item)
                time.sleep(0.1)
            if error_counter == 0:
                self.frame.zabbix_instance.metric[self.frame.zabbix_instance.idx] = 0
                self.frame.clear_error_led()
            else:
                self.frame.zabbix_instance.metric[self.frame.zabbix_instance.idx] = 1
                self.frame.set_error_led()

        except Exception as Err:
            self.logger_.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            self.frame.set_error_led()


    def syncs_thread(self):
        try:
            sleep_time = int(self.configs['check_all_files_interval'])
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
        except Exception as Err:
            self.logger_.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            self.frame.set_error_led()
        

    def start_timesync_thread(self):
        
        """        Método que inicia um thread de envio de metricas para o zabbix"""

        u = Thread(target=self.syncs_thread, args=[], daemon=True)
        u.start()
    

    def event_operations(self, filepath_source, path_dest, sync_name, event):

        """Método reproduzido quando um evento é detectado em algum diretório monitorado"""

        self.frame.status['evento_acontecendo'] = True
        while self.frame.status['sincronizando'] == True:
            self.frame.set_event_waiting_led()
            time.sleep(0.1) 
        self.frame.set_event_in_progress_led()
        try: 
            sync_ext = (self.configs['folders_to_sync'][sync_name]['sync_extensions'])
        except:
            sync_ext = []
        try:
            filename = str(os.path.basename(filepath_source)).lower()
            filepath_dest = os.path.join(path_dest, filename)
            if os.path.isfile(filepath_source) or os.path.isfile(filepath_dest):
                if (os.path.splitext(filename)[1][1:].lower() in sync_ext.lower) or (len(sync_ext) == 0):    
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
            self.frame.update_logs()
            self.frame.clear_event_in_progress_led()
        except Exception as Err:
            self.logger_.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            self.frame.zabbix_instance.metric = 1
        self.frame.status['evento_acontecendo'] = False


if __name__ == '__main__':
#    import parse_config
    import wx

    '''Carregando informações do diretório raiz do projeto'''
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

    '''Carregando configurações...'''
#    configuration = parse_config.ConfPacket()
#    configs = configuration.load_config('SYNC_FOLDERS, SYNC_TIMES, SYNC_EXTENSIONS, ZABBIX, SYNC_NAME')
     
    '''Variavel de status do sistema'''
    status = {
            'sincronizando' : False,
            'evento_acontecendo' : False,
            'updating_logs' : False
        }

    """Criando objeto de adição de registros de log"""
    logger_ = FileLogger_(pasta_de_logs='logs')

    '''Organizando parametros do zabbix'''
#    zabbix_param = {
#        'HOSTNAME' : configs['ZABBIX']['hostname'],
#        'SERVER' : configs['ZABBIX']['zabbix_server'],
#        'PORT' : int(configs['ZABBIX']['port']),
#        'KEY' : configs['ZABBIX']['key'],
#        'METRICS_INTERVAL' : int(configs['ZABBIX']['send_metrics_interval'])
#    }

    """Criando objeto de envio de metricas para o zabbix"""
 #   zsender = ZabbixSender_(
 #       metric_interval= zabbix_param['METRICS_INTERVAL'], 
 #       hostname= zabbix_param['HOSTNAME'], 
 #       key= zabbix_param['KEY'], 
 #       server= zabbix_param['SERVER'],
 #       port= zabbix_param['PORT'],
 #       idx= 0,
 #       metric= [0]
 #   )

    """Inicializando a interface gráfica"""
#    app = wx.App()  
#    frame = MyFrame(status=status, logger_=logger_, zabbix_instance= zsender, configs=configs)       # Janela principal

#    fileoperations_ = FileOperations_(configs, frame, logger_)
#    fileoperations_.start_timesync_thread()
#    while 1:
#        pass
#        time.sleep(1)
#        fileoperations_.aguarda_liberar_arquivo('C:\\teste2\\doc.txt')
#        print(fileoperations_.aguarda_liberar_arquivo.__name__)

      