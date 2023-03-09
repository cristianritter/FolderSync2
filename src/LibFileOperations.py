import time
import shutil
import os
import sys
from LibFileLogger import FileLogger_
from LibFrameClass import MyFrame
import json


class FileOperations_():
    def __init__(self, config_dict: dict, frame_inst: MyFrame, logger_inst: FileLogger_):
        """Inicialização da classe"""
        self.configs = config_dict
        self.frame = frame_inst
        self.logger_ = logger_inst
        
    def read_json_from_file(self, filename):                # Carrega um arquivo json para a memória e retorna um dict
        """     Carrega o conteúdo de um arquivo no formato Json para um dicionário"""
        try:
            with open(filename, 'r', encoding='utf-8') as infile:
                data = json.load(infile)
            return data
        except Exception as Err:
            print(f'$Error carregando arquivo json. Filename: {filename}, Erro: {Err}')
            return 0

    def wait_for_the_file_to_be_get_ready_for_copy(self, filepath_source):
        """Método que verifica se a criação do arquivo já foi finalizada antes de executar a cópia \n
        Retorna True se o arquivo estiver preso e não pode ser aberto por algum motivo desconhecido."""
        file_content = None
        time_begin = round(time.time())
        source_size1 = os.path.getsize( str(filepath_source) )
        time.sleep(0.02)                                        
        source_size2 = os.path.getsize( str(filepath_source) )
        while file_content == None or source_size1 != source_size2:      # Compara o tamanho do arquivo de origem em dois instantes de tempo diferentes
            source_size1 = os.path.getsize( str(filepath_source) )  # arquivos prontos para cópia devem manter o mesmo tamanho 
            time.sleep(0.02)                                        
            source_size2 = os.path.getsize( str(filepath_source) ) 
            try:
                with open(filepath_source, "rb") as file_content:        # opening for [r]eading as [b]inary
                    time.sleep(0.02)                                # se a abertura for possível sem falhas está pronto para a cópia
            except:
                pass         
            if (round(time.time()) > ( time_begin + 20) ):
                self.logger_.adiciona_linha_log("Arquivo protegido contra gravacao por mais de 20 segundos, não permitindo a cópia.")
                return True
        return 0

    def get_filename_type(self, filename):
        """Retorna o tipo de um arquivo. Ex: txt, mp3, etc"""
        return os.path.splitext(filename)[1][1:].lower()

    def check_if_file_extension_is_set_to_be_synced(self, filename, sync_extensions):
        if (len(sync_extensions) == 0): # Retorna True se não existem restrições de extensões a serem sincronizadas
            return True
        return self.get_filename_type(filename).lower() in ' '.join(sync_extensions).lower() # Verifica se a extensão do arquivo está incluida em sync_extensions
                    
    def get_dir_files_list(self, filespath):
        """ Retorna uma lista com todos os nomes dos arquivos no diretorio"""
        try:
            all_filenames_list = []
            for e in os.scandir(filespath):          # scanner do diretório
                if e.is_file():                 # para cada arquivo encontrado:
                    all_filenames_list.append(e.name.lower()) #adiciona a lista
            return all_filenames_list
        except Exception as err:
            self.logger_.adiciona_linha_log(f'Problema em get_dir_files_list. $Error:{err}')
            return 1
        
    def remove_files_from_dest_if_not_in_source(self, source, dest, sync_extensions):
        """Verifica todos os arquivos do destino e verifica se estão na origem. Se não existirem na origem, exclui do destino."""
        source_files_list = self.get_dir_files_list(source)
        for file in self.get_dir_files_list(dest):
            dest_file = os.path.join(dest, file)
            if not self.check_if_file_extension_is_set_to_be_synced(dest_file, sync_extensions):
                continue
            if file not in source_files_list:       # Verifica se arquivos existentes na pasta de destino existem na pasta de origem
                try:
                    os.remove(dest_file)                    # Remove os arquivos que não existem na pasta de origem
                    self.logger_.adiciona_linha_log(f"Removido: {dest_file}")
                except Exception as Err:
                    self.logger_.adiciona_linha_log(f"$Error ao remover arquivo. Erro: {Err} ")

    def copy_files_from_source_if_not_in_dest(self, source, dest, sync_extensions):
        started_task_timestamp=round(time.time())         # Armazena o horário de inicio da tarefa no diretório atual    
        source_files_list = self.get_dir_files_list(source)
        dest_files_list = self.get_dir_files_list(dest)         # Se tentar checkar cada arquivo individualmente demora demais
        for file in source_files_list:
            source_file = os.path.join(source, file)
            dest_file = os.path.join(dest, file)
            if not self.check_if_file_extension_is_set_to_be_synced(dest_file, sync_extensions):
                continue
            if not file in dest_files_list or self.get_file_modification_timestamp(dest_file) != self.get_file_modification_timestamp(source_file): 
                self.copy_file(source_file, dest_file)
            if (round(time.time()) > ( started_task_timestamp + 120) ):               # Passa para o próximo diretório caso a rotina passe de 2 minutos nesta pasta
                return 0
         
    def check_all_files_and_remove_if_files_are_not_equals(self, source, dest, sync_extensions):
        source_files_list = self.get_dir_files_list(source)
        for file in source_files_list:
            source_file = os.path.join(source, file)
            dest_file = os.path.join(dest, file)
            if not self.check_if_file_extension_is_set_to_be_synced(dest_file, sync_extensions):
                continue
            self.check_and_remove_if_both_files_are_not_same_size(source_file, dest_file)
            
    def copy_file(self, source_filename, dest_filename):
        if self.wait_for_the_file_to_be_get_ready_for_copy(source_filename):       # Se o arquivo estiver preso e a cópia for impedida retorna erro 1
            return 1  
        if os.path.isfile(dest_filename):
            self.logger_.adiciona_linha_log(f"Sobrescrito: {source_filename} to {dest_filename} ")                   
        else:
            self.logger_.adiciona_linha_log(f"Copiado: {source_filename} to {dest_filename} ")      
        shutil.copy2(source_filename, dest_filename)                # Copia o arquivo                              

    def get_file_modification_timestamp(self, file):
        return os.path.getmtime(file)

    def sync_source_content_to_dest_dir(self, source, dest, sync_extensions):
        """Sincroniza dois diretórios, copiando e/ou excluindo arquivos conforme a necessidade"""  
        try:
            debug = 'remove files'   
            self.remove_files_from_dest_if_not_in_source(source, dest, sync_extensions)
            self.copy_files_from_source_if_not_in_dest(source, dest, sync_extensions)
            self.check_all_files_and_remove_if_files_are_not_equals(source, dest, sync_extensions)
            return 0
        except Exception as err:
            self.logger_.adiciona_linha_log(f'Problema durante a rotina de sync_source_content_to_dest_dir. $Error:{err} debug:{debug}')
            return 1

    def wait_til_current_event_operaration_ends(self):
        self.frame.set_led2_orange()
        self.frame.status['sincronizando'] = True
        while self.frame.status['evento_acontecendo']:
            self.frame.status['sincronizando'] = False
            time.sleep(0.1)
        self.frame.set_led2_red()  
    
    def wait_til_current_timed_sync_ends(self):
        self.frame.status['evento_acontecendo'] = True
        self.frame.set_led1_orange()   
        while self.frame.status['sincronizando'] == True:
            time.sleep(0.1) 
        self.frame.set_led1_red()

    def set_zabbix_error(self):
        self.frame.zabbix_metric[0] = 1

    def reset_zabbix_error(self):
        self.frame.zabbix_metric[0] = 0
       
    def remove_file_from_dest_if_not_source(self, source_file, dest_file):
        if not os.path.exists(source_file):         # Se o arquivo não existe na origem, apaga no destino
            try:
                os.remove(dest_file)
                self.logger_.adiciona_linha_log("Removido: " + str(dest_file))
            except Exception as err:
                self.logger_.adiciona_linha_log(str(err) + "$Error ao remover arquivo. " + str(dest_file))
                self.frame.zabbix_metric[0] = 1
        
    def check_and_remove_if_both_files_are_not_same_size(self, source_file, dest_file):
        source_file_size = os.path.getsize(str(source_file))     #verifica o tamanho do arquivo de origem
        dest_file_size = os.path.getsize(str(dest_file))      # verifica o tamanho do arquivo de destino
        if (source_file_size != dest_file_size):
            os.remove(dest_file)
            self.logger_.adiciona_linha_log(f'Cópia corrompida. Será copiado novamente no próximo sync. $error {source_file}') 
            self.frame.zabbix_metric[0] = 1             

    def timed_sync_looping(self):
        try:
            while True:
                self.wait_til_current_event_operaration_ends()
                fails = 0
                for item in self.configs['folders_to_sync']:
                    origin_path, dest_path, sync_ext = self.configs['folders_to_sync'][item]['origem'], self.configs['folders_to_sync'][item]['destino'], self.configs['folders_to_sync'][item]['sync_extensions']      
                    fails += self.sync_source_content_to_dest_dir(origin_path, dest_path, sync_ext)          # error_counter soma 1 para cada evento de erro durante o sincronismo
                if not fails:
                    self.reset_zabbix_error()
                else:
                    self.logger_.adiciona_linha_log(f'$Error Não foi possível finalizar a sincronização de um ou mais diretório(s).')
                    self.set_zabbix_error()
                self.frame.status['sincronizando'] = False
                self.frame.set_led2_cinza()
                time.sleep(int(self.configs['check_all_files_interval']))
        except Exception as Err:
            self.logger_.adiciona_linha_log(f'$Error em timed_sync_looping: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            self.set_zabbix_error()

    def operation_fired_by_observer_event(self, filepath_source, path_dest, sync_name, event):
        """Método reproduzido quando um evento é detectado em algum diretório monitorado"""
        self.wait_til_current_timed_sync_ends()       
        try:
            sync_ext = self.configs['folders_to_sync'][sync_name]['sync_extensions']
            if self.check_if_file_extension_is_set_to_be_synced(filepath_source, sync_ext):      
                filename = str(os.path.basename(filepath_source)).lower()
                filepath_dest = os.path.join(path_dest, filename)     
                if os.path.isfile(filepath_dest):
                    self.remove_file_from_dest_if_not_source(filepath_source, filepath_dest)         # Remoção de arquivos
                elif os.path.isfile(filepath_source):
                    self.copy_file(filepath_source, filepath_dest)
                    self.check_and_remove_if_both_files_are_not_same_size(filepath_source, filepath_dest)                        
                else:
                    self.logger_.adiciona_linha_log(f'Evento não tratado pois o arquivo não existe mais na pasta de origem nem na pasta de destino: {event}')    
        except Exception as Err:
            self.logger_.adiciona_linha_log(f'$Error em: {sys._getframe().f_code.co_name}, Descrição: {Err}')
            self.set_zabbix_error()
        self.frame.panel_update()
        self.frame.set_led1_cinza()
        self.frame.status['evento_acontecendo'] = False

if __name__ == '__main__':
    pass
      