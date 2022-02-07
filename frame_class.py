import wx
import os
from datetime import datetime
import locale

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

task_icon = os.path.join(ROOT_DIR, 'task_icon.png')

def InitLocale(self):
    """
    Substituição do método padrão devido a problemas relacionados a detecção de locale no Windows 7.
    Não foi testado no windows 10.
    """
    self.ResetLocale()
    try:
        lang, _ = locale.getdefaultlocale()
        self._initial_locale = wx.Locale(lang, lang[:2], lang)
        locale.setlocale(locale.LC_ALL, 'portuguese_brazil')  #pulo do gato
    except (ValueError, locale.Error) as ex:
        target = wx.LogStderr()
        orig = wx.Log.SetActiveTarget(target)
        wx.LogError("Unable to set default locale: '{}'".format(ex))
        wx.Log.SetActiveTarget(orig)
wx.App.InitLocale = InitLocale   #substituindo metodo que estava gerando erro por um metodo vazio


class MyFrame(wx.Frame):    
    def __init__(self, status, logger_, zabbix_instance, configs):
        self.configs = configs      
        title_ = 'FolderSync by EngNSC - ' + self.configs['SYNC_NAME']['name']
        super().__init__(parent=None, title=title_, style=wx.CAPTION, pos=(5, 5), size=(1080, 600))  
        self.status = status
        self.logger_ = logger_
        self.zabbix_instance = zabbix_instance
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
        self.clear_btn.Bind(wx.EVT_LEFT_DOWN, self.clear_error_led)
        font = wx.Font(7, wx.DEFAULT, wx.FONTSTYLE_ITALIC, wx.BOLD, underline=True)
        self.clear_btn.SetFont(font)
        self.cb1 = wx.CheckBox(panel, label='Events View')
        self.cb1.SetValue(True)
        self.cb1.Bind(wx.EVT_CHECKBOX, self.update_logs)
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
        hide_button.Bind(wx.EVT_BUTTON, self.esconder_janela)            
        coluna.Add(linha_filter, 0, wx.CENTER) 
        coluna.Add(linha_led, 0, wx.CENTER) 
        coluna.Add(hide_button, 0, wx.TOP | wx.CENTER, 30)
        panel.SetSizer(coluna)
        self.Show()

    def esconder_janela(self, event):
        self.Hide()


    def set_event_in_progress_led(self, event=None):
        self.set_event_in_progress_led()
        self.Refresh()


    def set_event_waiting_led(self, event=None):
        self.led1.SetBackgroundColour('Yellow')
        self.Refresh()


    def clear_event_in_progress_led(self, event=None):
        self.led1.SetBackgroundColour('gray')
        self.Refresh()


    def set_sync_in_progress_led(self, event=None):
        self.led2.SetBackgroundColour('Red')
        self.Refresh()


    def set_sync_waiting_led(self, event=None):
        self.led2.SetBackgroundColour('Yellow')
        self.Refresh()


    def clear_sync_in_progress_led(self, event=None):
        self.led2.SetBackgroundColour('gray')
        self.Refresh()


    def set_error_led(self, event=None):
        self.led3.SetBackgroundColour('Red')
        self.Refresh()


    def clear_error_led(self, event=None):
        self.led3.SetBackgroundColour('gray')
        self.Refresh()


    def update_logs(self, event=None):
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


if __name__ == '__main__':
    
    import parse_config
    '''Carregando informações do diretório raiz do projeto'''
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    

    '''Carregando configurações...'''
    configuration = parse_config.ConfPacket()
    configs = configuration.load_config('SYNC_FOLDERS, SYNC_TIMES, SYNC_EXTENSIONS, ZABBIX, SYNC_NAME')

    
    status = {
        'sincronizando' : False,
        'evento_acontecendo' : False,
        'updating_logs' : False
    }
    zabbix_metric = [0]
    
    from FileLogger import FileLogger_
    logger_ = FileLogger_('logs')
    
    app = wx.App()  
 
    MyFrame_ = MyFrame(status, logger_, zabbix_metric, configs)
    app.MainLoop()