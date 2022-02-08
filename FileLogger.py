from datetime import datetime
import os
import sys


class FileLogger_:
    """Registrador de logs em arquivos.\n
    Recebe como argumento o nome da pasta onde os logs serão adicionados,\n
    essa pasta será criada dentro do diretorio raiz do programa."""  


    def __init__(self, pasta_de_logs):
        
        '''Inicialização da classe FileLogger'''
        
        self.LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), pasta_de_logs) 


    def checkDirectory(self, dir=None):
        
        '''Confere se o diretório existe, se não existir realiza a criação.'''
        
        try:
            if not os.path.isdir(dir):
                os.makedirs(dir)
        except Exception as Err:
            self.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')


    def adiciona_linha_log(self, *args):
        
        '''Método para adição de uma nova linha no arquivo de log \n
    Printa o conteúdo na tela e Adiciona um linha de log no estilo \
    f'{dataCompletaLog} - arg1 - args2 - argn \n '''
        
        '''Definindo strings com a data e hora atual que formam os dados a serem adicionados e o nome do arquivo corrente'''
        dataCompletaLog = datetime.now().strftime('%d/%m/%Y %H:%M:%S') 
        dataPartialLogFname = datetime.now().strftime('_%Y%m')

        '''Criação e impressão da linha de log'''
        LogDataContent = f"{dataCompletaLog} - {' - '.join(args)}"
        print(LogDataContent)
        
        try:
            self.checkDirectory(self.LOGS_DIR)
            logFilename = f'log{dataPartialLogFname}.txt'

            '''Abertura do arquivo e registro do conteúdo de log'''
            with open(os.path.join(self.LOGS_DIR, logFilename), "a") as file:
                file.write(f'{LogDataContent}\n')
            
        except Exception as Err:
            self.adiciona_linha_log(f'Erro em: {sys._getframe().f_code.co_name}, Descrição: {Err}')
         

if __name__ == '__main__':
    Logger = FileLogger_(pasta_de_logs='logs')
    Logger.adiciona_linha_log('arg1', 'arg2', 'arg3')
