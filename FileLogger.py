from datetime import datetime
import os

class FileLogger_:
    """Registrador de logs em arquivos.\n
    Recebe como argumento o nome da pasta onde os logs serão adicionados,\n
    essa pasta será criada dentro do diretorio raiz do programa."""  

    def __init__(self, pasta_de_logs):
        self.LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), pasta_de_logs) 

    def adiciona_linha_log(self, *args):
        
        """Adiciona um linha de log no estilo f'{dataFormatada} - arg1 - args2 - argn \n' """
        
        dataFormatada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        mes_ano = datetime.now().strftime('_%Y%m')

        texto = ""
        for item in args:
            texto += f' - {item}'

        print(dataFormatada, texto)
        
        try:
            if not os.path.isdir(self.LOGS_DIR):
                print('entrou')
                os.makedirs(self.LOGS_DIR)

            log_file = os.path.join(self.LOGS_DIR, f'log{mes_ano}.txt')
            f = open(log_file, "a")
            
            f.write(f'{dataFormatada}{texto}\n')
            f.close()

        except Exception as err:
            print(f'Erro durante registro no arquivo de log. {err}')
         
if __name__ == '__main__':
    Logger = FileLogger_(pasta_de_logs='logs')
    Logger.adiciona_linha_log('arg1', 'arg2', 'arg3')
