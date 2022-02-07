import wx
import os
import parse_config
import datetime, time
import shutil


from FileLogger import FileLogger



ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
configuration = parse_config.ConfPacket()
configs = configuration.load_config('SYNC_NAME, SYNC_TIMES')

task_icon = os.path.join(ROOT_DIR, 'task_icon.png')
sleep_time = int(configs['SYNC_TIMES']['sync_with_no_events_time'])  
title_ = 'FolderSync by EngNSC - ' + configs['SYNC_NAME']['name']


class MyFrame(wx.Frame):    
    def __init__(self, status, logger_, zabbix_metric):
        super().__init__(parent=None, title=title_, style=wx.CAPTION, pos=(5, 5), size=(1080, 600))        
        self.status = status
        self.logger_ = logger_
        self.SetIcon(wx.Icon(task_icon))
        panel = wx.Panel(self)
        coluna = wx.BoxSizer(wx.VERTICAL) 
        font = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.title_txt = wx.StaticText(panel, label='FolderSync')
        self.title_txt.SetFont(font)
        font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD, underline=True)
        self.subtitle_txt = wx.StaticText(panel, label='- Log de eventos -')
        self.subtitle_txt.SetFont(font)
        linha_titulo = wx.BoxSizer(wx.HORIZONTAL)
        linha_titulo.Add(self.title_txt, 0, wx.TOP, 20)
        linha_titulo.AddSpacer(30)
        linha_titulo.Add(self.subtitle_txt, 0, wx.TOP, 30)
        self.led1 =  wx.StaticText(panel, wx.ID_ANY, label='', size=(20,15))
        self.ld1txt = wx.StaticText(panel, label='Event in progress')
        self.led2 =  wx.StaticText(panel, wx.ID_ANY, "", size=(20,15))
        self.ld2txt = wx.StaticText(panel, label='All Sync in progress')
        self.led3 =  wx.StaticText(panel, wx.ID_ANY, "", size=(20,15))
        self.ld3txt = wx.StaticText(panel, label='Error detected')
        self.led1.SetBackgroundColour('gray')
        self.led2.SetBackgroundColour('gray')
        self.led3.SetBackgroundColour('gray')
        self.clear_btn = wx.StaticText(panel, label='(Limpar Erros)')
        self.clear_btn.Bind(wx.EVT_LEFT_DOWN, self.on_clean)
        font = wx.Font(7, wx.DEFAULT, wx.FONTSTYLE_ITALIC, wx.BOLD, underline=True)
        self.clear_btn.SetFont(font)
        self.cb1 = wx.CheckBox(panel, label='Events View')
        self.cb1.SetValue(True)
        self.cb1.Bind(wx.EVT_CHECKBOX, self.check_events, self.cb1)
        self.logpanel = wx.TextCtrl(panel, value='Ainda não existe um log disponível este mês.', style=wx.TE_MULTILINE | wx.TE_READONLY, size=(50,400))
        coluna.Add(linha_titulo, 0, wx.CENTER)
        coluna.AddSpacer(10)
        coluna.Add(self.logpanel, 0, wx.ALL | wx.EXPAND, 2) 
        linha_filter = wx.BoxSizer(wx.HORIZONTAL)
        linha_filter.Add(self.cb1, 0, wx.TOP, 5)
        linha_led = wx.BoxSizer(wx.HORIZONTAL)
        linha_led.Add(self.led1, 0, wx.TOP, 5)
        linha_led.AddSpacer(10)
        linha_led.Add(self.ld1txt, 0, wx.TOP, 5)
        linha_led.AddSpacer(20)
        linha_led.Add(self.led2, 0, wx.TOP, 5)
        linha_led.AddSpacer(10)
        linha_led.Add(self.ld2txt, 0, wx.TOP, 5)
        linha_led.AddSpacer(20)
        linha_led.Add(self.led3, 0, wx.TOP, 5)
        linha_led.AddSpacer(10)
        linha_led.Add(self.ld3txt, 0, wx.TOP, 5)
        linha_led.AddSpacer(20)
        linha_led.Add(self.clear_btn, 0, wx.TOP, 10)
        hide_button = wx.Button(panel, label='Fechar')
        hide_button.Bind(wx.EVT_BUTTON, self.on_press)            
        coluna.Add(linha_filter, 0, wx.CENTER) 
        coluna.Add(linha_led, 0, wx.CENTER) 
        coluna.Add(hide_button, 0, wx.TOP | wx.CENTER, 30)
        panel.SetSizer(coluna)
        self.Show()

    def check_events(self, event):
        self.update_logs()
        
    def on_press(self, event):
        self.Hide()
    
    def on_clean(self, event):
        self.led3.SetBackgroundColour('gray')
        self.Refresh()

    def set_error_led(self):
        self.led3.SetBackgroundColour('Red')
        self.Refresh()

    def update_logs(self):
        if self.status['updating_logs']:
            return
        self.status['updating_logs'] = True
        mes_ano = datetime.now().strftime('_%Y%m')
        log_file = 'log'+mes_ano+'.txt'
        
        log_pathfile = os.path.join(ROOT_DIR, 'logs', log_file)
        if not os.path.exists(log_pathfile):
            self.status['updating_logs'] = False
            return

        f = open(log_pathfile, "r")
        linhas = f.readlines(20000000)
        linhas.reverse()
        remover=[]
        if (self.cb1.GetValue() == False):
            for item in linhas:
                if ('<' in item):
                    remover.append(item)
            for item in remover:
                linhas.remove(item)
        self.logpanel.SetValue(''.join(linhas))
        self.status['updating_logs'] = False

    def syncs_thread(self):
        while sleep_time > 0:
            self.led2.SetBackgroundColour('yellow')
            self.Refresh()
            self.status['sincronizando'] = True
            if self.status['evento_acontecendo']:
                self.status['sincronizando'] = False
                time.sleep(1)
                continue
            self.led2.SetBackgroundColour('Red')
            self.Refresh()
            self.sync_all_folders()
            self.status['sincronizando'] = False
            self.led2.SetBackgroundColour('gray')
            self.Refresh()
            time.sleep(sleep_time)

    def sync_all_folders(self):
        try:
            self.update_logs()
            error_counter = 0
            for item in configs['SYNC_FOLDERS']:
                time.sleep(0.1)
                path = (configs['SYNC_FOLDERS'][item]).split(', ')
                error_counter += self.filetree(path[0], path[1], item)
                time.sleep(0.1)
            if error_counter == 0:
                self.zabbix_metric = 0
        except Exception as err:
            self.logger_.adiciona_linha_log("Falha durante execução da função sync_all_folders - "+str(err))
            self.set_error_led()

    def filetree(self, source, dest, sync_name):
        
        files_destination_md5=dict()
        files_source_md5=dict()
        try: 
            sync_ext = configs['SYNC_EXTENSIONS'][sync_name].lower().split(", ")
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
                        self.set_error_led()

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
            self.zabbix_metric = str(source) 
            self.logger_.adiciona_linha_log(str(err)+debug)
            return 1

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
                self.set_error_led()
                break
        try:
            in_file.close()            
        except:
            pass

if __name__ == '__main__':
    status = {
        'sincronizando' : False,
        'evento_acontecendo' : False,
        'updating_logs' : False
    }
    zabbix_metric = [0]

    logger_ = FileLogger('logs')
    app = wx.App()  
 
    MyFrame_ = MyFrame(status, logger_, zabbix_metric)
    app.MainLoop()