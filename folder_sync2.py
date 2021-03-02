import time
import logging
import shutil
import parse_config
import os
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from datetime import date, datetime
from pyzabbix import ZabbixMetric, ZabbixSender
from threading import Thread
import wx.adv
import wx
try:    
    print('Carregando configurações...')
    configuration = parse_config.ConfPacket()
    configs = configuration.load_config('SYNC_FOLDERS, LOG_FOLDER, SYNC_TIMES, SYNC_EXTENSIONS, ZABBIX, SYNC_NAME')

    TRAY_TOOLTIP = 'FolderSync - ' + configs['SYNC_NAME']['name']
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    TRAY_ICON = 'icon.png' 
    diretorio = os.path.join(ROOT_DIR, TRAY_ICON)

    def create_menu_item(menu, label, func):
        item = wx.MenuItem(menu, -1, label)
        menu.Bind(wx.EVT_MENU, func, id=item.GetId())
        menu.Append(item)
        return item

    class TaskBarIcon(wx.adv.TaskBarIcon):
        def __init__(self, frame):
            self.frame = frame
            super(TaskBarIcon, self).__init__()
            self.set_icon(diretorio)
            self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

        def CreatePopupMenu(self):
            menu = wx.Menu()
            create_menu_item(menu, 'Abrir log', self.on_hello)
            menu.AppendSeparator()
            create_menu_item(menu, 'Exit', self.on_exit)
            return menu

        def set_icon(self, path):
            icon = wx.Icon(path)
            self.SetIcon(icon, TRAY_TOOLTIP)

        def on_left_down(self, event):      
            frame.Show()
            
        def on_hello(self, event):
            frame.Show()

        def on_exit(self, event):
            wx.CallAfter(self.Destroy)
            self.frame.Close()
            

    class MyFrame(wx.Frame):    
        def __init__(self):
            title_ = 'FolderSync by EngNSC - ' + configs['SYNC_NAME']['name']
            super().__init__(parent=None, title=title_, style=wx.CAPTION, pos=(5, 5), size=(1080, 800))        
            panel = wx.Panel(self)
            my_sizer = wx.BoxSizer(wx.VERTICAL) 
            font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
            self.st2 = wx.StaticText(panel, label='Visualização de eventos')
            self.st2.SetFont(font)
            self.st1 = wx.TextCtrl(panel, value='Ainda não existe um log disponível este mês.', style=wx.TE_MULTILINE | wx.TE_READONLY, size=(50,650))
            my_sizer.Add(self.st2, 0, wx.ALL | wx.CENTER, 10) 
            my_sizer.Add(self.st1, 0, wx.ALL | wx.EXPAND, 10) 
            my_btn = wx.Button(panel, label='Ocultar')
            my_btn.Bind(wx.EVT_BUTTON, self.on_press)
            my_sizer.Add(my_btn, 0, wx.ALL | wx.CENTER, 5)   
            panel.SetSizer(my_sizer)
        # self.SetDimensions(0,0,640,480)
            self.Show()

        def on_press(self, event):
            frame.Hide()


    metric_value = 0

    print("Definindo classes...")

    class Event(LoggingEventHandler):
        try:
            def dispatch(self, event): 
                LoggingEventHandler()
                adiciona_linha_log(str(event))
                path_event = str(event.src_path)
                for sync in configs['SYNC_FOLDERS']:
                    paths = (configs['SYNC_FOLDERS'][sync]).split(', ')
                    if paths[0] in path_event:
                        event_operations(path_event, paths[1], sync, event)
                update_logs()
                
        except Exception as err:
            adiciona_linha_log("Logging event handler erro - "+str(err))

    print('Definindo funções...')

    def send_status_metric():
        while 1:
            time.sleep(int(configs['ZABBIX']['send_metrics_interval']))
            global metric_value
            value = metric_value
            '''
            Envia metricas para zabbix:
                ---Em caso de erro de sinc -> envia str com caminho do diretório que ocorreu o erro [strlen > 1]
                ---Em caso de sucesso nas rotinas -> envia flag str com '0' [strlen == 1]
                ---Após sincronizar todas as pastas da lista envia flag str com '1' [strlen == 1]
            '''
            try:
                packet = [
                    ZabbixMetric(configs['ZABBIX']['hostname'], configs['ZABBIX']['key'], value)
                ]
                ZabbixSender(zabbix_server=configs['ZABBIX']['zabbix_server'], zabbix_port=int(configs['ZABBIX']['port'])).send(packet)
            except Exception as err:
                adiciona_linha_log("Falha de conexão com o Zabbix - "+str(err))

    def adiciona_linha_log(texto):
        dataFormatada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        mes_ano = datetime.now().strftime('_%Y%m')
        print(dataFormatada, texto)
        try:
            log_file = configs['LOG_FOLDER']['log_folder']+'log'+mes_ano+'.txt'
            f = open(log_file, "a")
            f.write(dataFormatada + ' ' + texto +"\n")
            f.close()
        except Exception as err:
            print(dataFormatada, err)
            
    def getfilename(filepath):
        try:
            pathlist = filepath.split('\\')
            filename = (pathlist[len(pathlist)-1]).lower()
            return (filename)
        except Exception as Err:
            adiciona_linha_log(str(Err)+'Getfilename')

    def filetree(source, dest, sync_name):
        files_destination_md5=dict()
        files_source_md5=dict()
        try: 
            sync_ext = configs['SYNC_EXTENSIONS'][sync_name].lower().split(", ")
            print(sync_ext)
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
                    os.remove(path_dest)
                    adiciona_linha_log("Removido: " + str(path_dest))
                    files_to_remove.append(file)

            debug = 'destination.pop'  
            for item in files_to_remove:
                files_destination_md5.pop(item)

            debug = 'copy files'
            for file in files_source_md5:
                path_source = os.path.join(source, file)
                path_dest = os.path.join(dest, file)
                if file not in files_destination_md5:
                    shutil.copy2(path_source, path_dest)                
                    adiciona_linha_log("Copiado: " + str(path_source) + " to " + str(path_dest))
                else:            
                    if files_source_md5[file] != files_destination_md5[file]:
                        shutil.copy2(path_source, path_dest)
                        adiciona_linha_log("Sobrescrito: " + str(path_source) + " to " + str(path_dest))
            return 0

        except Exception as err:
            global metric_value
            metric_value = str(source) 
            adiciona_linha_log(str(err)+debug)
            return 1

    def event_operations(filepath_source, path_dest, sync_name, event):
        try: 
            sync_ext = configs['SYNC_EXTENSIONS'][sync_name].lower().split(", ")
        except:
            sync_ext = []

        try:
            filename = getfilename(filepath_source).lower()
            filepath_dest = os.path.join(path_dest, filename)

            if 'FileMovedEvent' in str(event):
                adiciona_linha_log("Renomeado: " + str(event.src_path) + ' to ' + str(event.dest_path))
                shutil.copy2(str(event.dest_path), (os.path.join(   path_dest, getfilename(str(event.dest_path))   )))
                adiciona_linha_log("Copiado: " + str(event.dest_path) + " to " + (os.path.join(   path_dest, getfilename(str(event.dest_path))     )))   
        
            if os.path.isfile(filepath_source) or os.path.isfile(filepath_dest):
                if (not os.path.splitext(filename)[1][1:].lower() in sync_ext) & (len(sync_ext) > 0):
                    return
                if not os.path.exists(filepath_source):
                    os.remove(filepath_dest)
                    adiciona_linha_log("Removido: " + str(filepath_dest))
                elif not os.path.exists(filepath_dest):
                    shutil.copy2(filepath_source, filepath_dest)
                    adiciona_linha_log("Copiado: " + str(filepath_source) + " to " + str(filepath_dest))   
                else:
                    source_mtime = os.stat(filepath_source).st_mtime
                    dest_mtime = os.stat(filepath_dest).st_mtime
                    if source_mtime != dest_mtime:
                        shutil.copy2(filepath_source, filepath_dest)
                        adiciona_linha_log("Sobrescrito: " + str(filepath_source) + " to " + str(filepath_dest))

        except Exception as Err:
            adiciona_linha_log(str(Err)) 
            global metric_value
            metric_value = str(filepath_source)

    def sync_all_folders():
        try:
            error_counter = 0
            for item in configs['SYNC_FOLDERS']:
                path = (configs['SYNC_FOLDERS'][item]).split(', ')
                error_counter += filetree(path[0], path[1], item)
                time.sleep(0.2)
            if error_counter == 0:
                global metric_value
                metric_value = 0

        except Exception as err:
            adiciona_linha_log("Falha durante execução da função sync_all_folders - "+str(err))

    def update_logs():
        global frame
        mes_ano = datetime.now().strftime('_%Y%m')
        log_file = configs['LOG_FOLDER']['log_folder']+'log'+mes_ano+'.txt'
        if not os.path.exists(log_file):
            return
        f = open(log_file, "r")
        linhas = f.readlines(20000000)
        linhas.reverse()
        frame.st1.SetValue(' '.join(linhas))
    
    def syncs_thread():
        while True:
            sleep_time = int(configs['SYNC_TIMES']['sync_with_no_events_time'])
            if (sleep_time > 0):
                time.sleep(sleep_time)
                sync_all_folders()
            else:
                time.sleep(30)


    if __name__ == "__main__":

        print("Inicializando sistema de logging..")
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        
        event_handler = Event()
        observer = Observer()
        
        for item in configs['SYNC_FOLDERS']:
            try:
                host = (configs['SYNC_FOLDERS'][item]).split(', ')
                observer.schedule(event_handler, host[0], recursive=False)
            except Exception as err:
                adiciona_linha_log(str(err)+host[0])

        observer.start()
        
        try:      
            app = wx.App()
            frame = MyFrame()
            TaskBarIcon(frame)
            t = Thread(target=syncs_thread, daemon=True)
            u = Thread(target=send_status_metric, daemon=True)
            t.start()
            u.start()
            update_logs()
            app.MainLoop()

        except KeyboardInterrupt:
            observer.stop()
        
        #observer.join()
except Exception as ERR:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    dire = os.path.join(ROOT_DIR, 'ERRO.TXT')
    f = open(dire, "a")
    f.write(str(ERR))
    f.close()
   


