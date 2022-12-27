import time
import shutil
import os
import sys
from LibFileLogger import FileLogger_
from LibFrameClass import MyFrame
import json


class FileOperations_():
    def __init__(self, config_dict: dict, frame_inst: MyFrame, logger_inst: FileLogger_) -> bool:
        """Inicialização da classe"""
        self.configs = config_dict
        self.frame = frame_inst
        self.logger_ = logger_inst
    
    def read_json_from_file(self, filename):                # Carrega um arquivo json para a memória e retorna um dict
        """     Carrega o conteúdo de um arquivo no formato Json para um dicionário"""
        try:
            """Le dados do arquivo"""
            with open(filename, 'r', encoding='utf-8') as infile:
                data = json.load(infile)
            return data
        except Exception as Err:
            print(f'Erro carregando arquivo json. Filename: {filename}, Erro: {Err}')
            return 0

    def aguarda_liberar_arquivo(self, filepath_source):
        """Método que verifica se a criação do arquivo já foi finalizada antes de executar a cópia \n
        Retorna True se o arquivo estiver preso e não pode ser aberto por algum motivo desconhecido."""
        file_content = None
        time_begin = round(time.time())
        source_size1 = os.path.getsize( str(filepath_source) )
        source_size2 = os.path.getsize( str(filepath_source) )
        while file_content == None or source_size1 != source_size2:      # Compara o tamanho do arquivo de origem em dois instantes de tempo diferentes
            source_size1 = os.path.getsize( str(filepath_source) )  # arquivos prontos para cópia devem manter o mesmo tamanho 
            time.sleep(0.02)                                        # in file conterá o arquivo se estiver liberado para abertura
            source_size2 = os.path.getsize( str(filepath_source) ) 
            try:
                with open(filepath_source, "rb") as file_content:        # opening for [r]eading as [b]inary
                    time.sleep(0.02)                                # se a abertura for possível sem falhas está pronto para a cópia
            except:
                pass         
            if (round(time.time()) > ( time_begin + 20) ):
                self.logger_.adiciona_linha_log("Arquivo protegido contra gravacao por mais de 20 segundos, não permitindo a cópia.")
                return True
        return False

    def getfilelistbymodiftime(self, filespath, sync_extensions):
        files_last_modif_dict = {}
        for e in os.scandir(filespath):          # scanner do diretório
            if e.is_file():                 # para cada arquivo encontrado:
                if (not os.path.splitext(e.name)[1][1:].lower() in ' '.join(sync_extensions).lower()) & (len(sync_extensions) > 0):
                    continue                # ignora o arquivo se não estiver na lista de extensões a serem trabalhadas
                files_last_modif_dict[e.name.lower()]=e.stat().st_mtime       # verifica a data de modificacao do arquivo e adiciona a lista
        return files_last_modif_dict

    def folder_mirror(self, source, dest, sync_extensions):
        """Sincroniza dois diretórios, copiando e/ou excluindo arquivos conforme a necessidade"""  
        destfile_lastmodif_dict=dict()                # Contém a lista de arquivos da pasta de destino. ->    Key=filename, value=timeoflastmodification
        sourcefile_lastmodif_dict=dict()                     # Contém a lista de arquivos da pasta de origem.  ->    Key=filename, value=timeoflastmodification
        try:
            debug = 'scan source and dest folders'             # identificação do ponto de execução para verificação de falhas
            destfile_lastmodif_dict = self.getfilelistbymodiftime(dest, sync_extensions)
            sourcefile_lastmodif_dict = self.getfilelistbymodiftime(source, sync_extensions)       
            debug = 'remove files'
            removed_files = []
            for file in destfile_lastmodif_dict:
                path_dest = os.path.join(dest, file)
                if file not in sourcefile_lastmodif_dict:       # Verifica se arquivos existentes na pasta de destino existem na pasta de origem
                    try:
                        os.remove(path_dest)                    # Remove os arquivos que não existem na pasta de origem
                        removed_files.append(file)
                        self.logger_.adiciona_linha_log(f"Removido: {path_dest}")
                    except Exception as Err:
                        self.logger_.adiciona_linha_log(f"Erro ao remover arquivo. Erro: {Err} Debug: {debug}")
            for item in removed_files:                  # precisa ser feito assim pq o dict não pode ser alterado dentro do loop for
                destfile_lastmodif_dict.pop(item)       # Remove arquivos apagados da lista de arquivos existentes                
            debug = 'copy files'
            thistime=round(time.time())
            for file in sourcefile_lastmodif_dict:
                path_source = os.path.join(source, file)
                path_dest = os.path.join(dest, file)
                                                                # Se o arquivo não estiver na lista de destino ou tiver tamanho diferente:
                if file not in destfile_lastmodif_dict or sourcefile_lastmodif_dict[file] != destfile_lastmodif_dict[file]:    
                    if self.aguarda_liberar_arquivo(path_source):       # Se o arquivo estiver preso e a cópia for impedida retorna erro 1
                        return 1
                    shutil.copy2(path_source, path_dest)                # Copia o arquivo              
                    if file not in destfile_lastmodif_dict:     # Se arquivo não existia adiciona informação de cópia
                        self.logger_.adiciona_linha_log(f"Copiado: {path_source} [{os.path.getsize(str(path_source))} bytes] to {path_dest} [{os.path.getsize(str(path_dest))} bytes.]")
                    else:                                       # Se existia adiciona informação de sobrescrita
                        self.logger_.adiciona_linha_log(f"Sobrescrito: {path_source} [{os.path.getsize(str(path_source))} bytes] to {path_dest} [{os.path.getsize(str(path_dest))} bytes.]")         
                if (round(time.time()) > ( thistime + 120) ):               # Passa para o próximo diretório caso a rotina passe de 2 minutos nesta pasta
                    return 0                                                # Retorna automaticamente no próximo ciclo
            return 0
        except Exception as err:
            self.logger_.adiciona_linha_log(f'Problema durante a rotina de folder_mirror. Erro:{err} debug:{debug}')
            return 1

    def timed_sync_looping(self):
        try:
            while True:
                self.frame.set_led2_orange()
                self.frame.status['sincronizando'] = True
                if self.frame.status['evento_acontecendo']:
                    self.frame.status['sincronizando'] = False
                    time.sleep(1)
                    continue
                self.frame.set_led2_red()  
                try:
                    error_counter = 0
                    for item in self.configs['folders_to_sync']:
                        time.sleep(0.1)
                        origin_path = self.configs['folders_to_sync'][item]['origem']  #diretorio de origem
                        dest_path = self.configs['folders_to_sync'][item]['destino'] # diretorio de destino
                        try: 
                            sync_ext : list = self.configs['folders_to_sync'][item]['sync_extensions']
                        except:
                            sync_ext = []
                        error_counter += self.folder_mirror(origin_path, dest_path, sync_ext)          # error_counter soma 1 para cada evento de erro durante o sincronismo
                        time.sleep(0.1)
                    if error_counter == 0:
                        self.frame.zabbix_metric[0] = 0
                        self.frame.clear_error_led()
                    else:
                        self.logger_.adiciona_linha_log(f'Erro durante a sincronização de {error_counter} diretório(s).')
                        self.frame.zabbix_metric[0] = 1
                        self.frame.set_error_led()
                except Exception as Err:
                    self.logger_.adiciona_linha_log(f'Erro em sync_all_folders: {sys._getframe().f_code.co_name}, Descrição: {Err}')
                    self.frame.zabbix_metric[0] = 1
                    self.frame.set_error_led()               

                self.frame.status['sincronizando'] = False
                self.frame.set_led2_cinza()
                self.frame.panel_update()
                sleep_time = int(self.configs['check_all_files_interval'])
                time.sleep(sleep_time)
        except Exception as Err:
            self.logger_.adiciona_linha_log(f'Erro em Fileoperations.syncs thread: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            self.frame.zabbix_metric[0] = 1
            self.frame.set_error_led()

    def event_operations(self, filepath_source, path_dest, sync_name, event):
        """Método reproduzido quando um evento é detectado em algum diretório monitorado"""
        self.frame.status['evento_acontecendo'] = True
        self.frame.set_led1_orange()
        while self.frame.status['sincronizando'] == True:
            time.sleep(0.1) 
        self.frame.set_led1_red()
        try: 
            sync_ext = self.configs['folders_to_sync'][sync_name]['sync_extensions']
        except:
            sync_ext = []
        try:
            filename = str(os.path.basename(filepath_source)).lower()
            filepath_dest = os.path.join(path_dest, filename)
            if os.path.isfile(filepath_source) or os.path.isfile(filepath_dest):
                if (os.path.splitext(filename)[1][1:].lower() in ' '.join(sync_ext).lower() or len(sync_ext) == 0):  # Se a extensao do arquivo estiver entre as sincronizadas  
                    """Remoção de arquivos"""
                    if not os.path.exists(filepath_source):         # Se o arquivo não existe na origem, apaga no destino
                        try:
                            os.remove(filepath_dest)
                            self.logger_.adiciona_linha_log("Removido: " + str(filepath_dest))
                        except Exception as err:
                            self.logger_.adiciona_linha_log(str(err) + "Erro ao remover arquivo. " + str(filepath_dest))
                            self.frame.zabbix_metric[0] = 1
                            self.frame.set_error_led()       
                        """Cópia de arquivos"""
                    elif not os.path.exists(filepath_dest):         # Se o arquivo não existe no destino, copia para o destino
                        self.aguarda_liberar_arquivo(filepath_source)
                        shutil.copy2(filepath_source, filepath_dest)
                        self.logger_.adiciona_linha_log(f"Copiado: {filepath_source} [{os.path.getsize(str(filepath_source))} bytes] to {filepath_dest} [{os.path.getsize(str(filepath_dest))} bytes]")  
                    else:                                           # Se data de modificação ou tamanhos diferentes:
                        origem_size = os.path.getsize(str(filepath_source))
                        destino_size = os.path.getsize(str(filepath_dest))
                        source_mtime = os.stat(filepath_source).st_mtime
                        dest_mtime = os.stat(filepath_dest).st_mtime
                        if source_mtime != dest_mtime or origem_size != destino_size:
                            self.aguarda_liberar_arquivo(filepath_source)
                            shutil.copy2(filepath_source, filepath_dest)
                            self.logger_.adiciona_linha_log(f"Sobrescrito: {filepath_source} [{origem_size} bytes] to {filepath_dest} [{destino_size} bytes]")
                            if (origem_size != destino_size):
                                os.remove(filepath_dest)
                                self.logger_.adiciona_linha_log(f'Cópia corrompida. Será copiado novamente no próximo sync {filepath_source}') 
                                self.frame.zabbix_metric[0] = 1
                                self.frame.set_error_led()
            self.frame.panel_update()
            self.frame.set_led1_cinza()
        except Exception as Err:
            self.logger_.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            self.frame.zabbix_metric[0] = 1
            self.frame.set_led1_cinza()
        self.frame.status['evento_acontecendo'] = False

if __name__ == '__main__':
    import wx

    '''Carregando informações do diretório raiz do projeto'''
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

    '''Carregando configurações...'''
     
    '''Variavel de status do sistema'''
    status = {
            'sincronizando' : False,
            'evento_acontecendo' : False,
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

      