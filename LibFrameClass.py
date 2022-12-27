import wx
import os
from datetime import datetime
import locale
from LibFileLogger import FileLogger_

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
    def __init__(self, status, logger_: FileLogger_, zabbix_metric : list, configs: dict): 
        super().__init__(parent=None, style=wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION, pos=(5, 5), size=(1080, 680))  
        self.SetIcon(wx.Icon(task_icon))

        self.configs = configs      
        self.status = status
        self.logger_ = logger_
        self.zabbix_metric = zabbix_metric
        self.Title = f"FolderSync by EngNSC - {self.configs['trayicon_alias']}"

        """Criação do painel"""
        panel = wx.Panel(self)

        """Criação dos items da interface"""
        StaticTextTittle = wx.StaticText(panel, label='Log de Eventos')
      
        self.led1 =  wx.StaticText(panel, wx.ID_ANY, label='', size=(20,15))
        ld1txt = wx.StaticText(panel, label='Event in progress')
        self.led2 =  wx.StaticText(panel, wx.ID_ANY, "", size=(20,15))
        ld2txt = wx.StaticText(panel, label='All Sync in progress')
        self.led3 =  wx.StaticText(panel, wx.ID_ANY, "", size=(20,15))
        ld3txt = wx.StaticText(panel, label='Error detected')

        self.logpanel = wx.TextCtrl(panel, value='Ainda não existe um log disponível este mês.', style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1,-1))
        self.clear_btn = wx.StaticText(panel, label='(Limpar Erros)')
        self.cb1 = wx.CheckBox(panel, label='Visualização completa com descrição de eventos')
        self.cb1.SetValue(True)
        #hide_button = wx.Button(panel, label='Esconder')


        """Configuração de Fonts"""
        TittleFont = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        StaticTextTittle.SetFont(TittleFont)

        ButtonFont = wx.Font(7, wx.DEFAULT, wx.FONTSTYLE_ITALIC, wx.BOLD, underline=True)
        self.clear_btn.SetFont(ButtonFont)


        """Configuração de Items Colors"""    
        self.led1.SetBackgroundColour('gray')
        self.led2.SetBackgroundColour('gray')
        self.led3.SetBackgroundColour('gray')


        """Items Binds"""
        self.clear_btn.Bind(wx.EVT_LEFT_DOWN, self.clear_error_led)
        self.cb1.Bind(wx.EVT_CHECKBOX, self.filter_update)
        self.Bind(wx.EVT_CLOSE, self.on_hide)

    
        """Organização dos items [containers]"""
        
        linha_titulo = wx.BoxSizer(wx.HORIZONTAL)
        linha_titulo.Add(StaticTextTittle, 0, wx.ALL, border=5)
    
        linha_filter = wx.BoxSizer(wx.HORIZONTAL)
        linha_filter.Add(self.cb1, 0, wx.TOP, 5)

        linha_led = wx.BoxSizer(wx.HORIZONTAL)
        linha_led.Add(self.led1, 0, wx.ALL, border=5)
        linha_led.Add(ld1txt, 0, wx.ALL, border=5)
        linha_led.AddSpacer(20)
        linha_led.Add(self.led2, 0, wx.ALL, border=5)
        linha_led.Add(ld2txt, 0, wx.ALL, border=5)
        linha_led.AddSpacer(20)
        linha_led.Add(self.led3, 0, wx.ALL, border=5)
        linha_led.Add(ld3txt, 0, wx.ALL, border=5)
        linha_led.AddSpacer(20)
        linha_led.Add(self.clear_btn, 0, wx.ALL, border=5)
        
        coluna_todo_conteudo = wx.BoxSizer(wx.VERTICAL) 
        coluna_todo_conteudo.Add(linha_titulo, 0, wx.CENTER | wx.ALL, border=10)
        coluna_todo_conteudo.Add(self.logpanel, 1, wx.ALL | wx.EXPAND, 5) 
        coluna_todo_conteudo.Add(linha_filter, 0, wx.ALIGN_CENTER | wx.ALL, border=10) 
        coluna_todo_conteudo.Add(linha_led, 0, wx.CENTER | wx.ALL, border=20) 
       
        panel.SetSizer(coluna_todo_conteudo)
        self.Show()

    def on_hide(self, event):
        """Método que oculta a janela do programa para a bandeja do sistema"""
        self.Hide()


    def set_event_in_progress_led(self, event=None):

        """Método que troca a cor do sinalizador de evento em curso para vermelho"""

        self.led1.SetBackgroundColour('Red')
        self.Refresh()


    def set_event_waiting_led(self, event=None):

        """Método que troca a cor do sinalizador de evento em curso para amarelo """

        self.led1.SetBackgroundColour('Yellow')
        self.Refresh()


    def clear_event_in_progress_led(self, event=None):

        """Método que troca a cor do sinalizador de evento em curso para cinza"""

        self.led1.SetBackgroundColour('gray')
        self.Refresh()


    def set_sync_in_progress_led(self, event=None):

        """Método que troca a cor do sinalizador de sincronismo em curso para vermelho"""

        self.led2.SetBackgroundColour('Red')
        self.Refresh()


    def set_sync_waiting_led(self, event=None):

        """Método que troca a cor do sinalizador de sincronismo em curso para amarelo"""

        self.led2.SetBackgroundColour('Yellow')
        self.Refresh()


    def clear_sync_in_progress_led(self, event=None):

        """Método que troca a cor do sinalizador de sincronismo em curso para cinza"""

        self.led2.SetBackgroundColour('gray')
        self.Refresh()


    def set_error_led(self, event=None):

        """Método que troca a cor do sinalizador de erro ocorrido para vermelho"""

        self.led3.SetBackgroundColour('Red')
        self.Refresh()

    def clear_error_led(self, event=None):

        """Método que troca a cor do sinalizador de erro ocorrido para cinza"""

        self.led3.SetBackgroundColour('gray')
        self.Refresh()

    def get_log_data_lines(self):
        dataPartialLogFname = datetime.now().strftime('_%Y%m')
        logFilename = f'log{dataPartialLogFname}.txt'
        
        log_pathfile = os.path.join(ROOT_DIR, 'logs', logFilename)
        
        if not os.path.exists(log_pathfile):            #sai da função se o arquivo nao existir por alguma razão
            self.status['updating_logs'] = False
            return 0

        with open(log_pathfile, "r") as file:
            linhas = file.readlines(20000000)
        
        linhas.reverse()        #reverse pois os logs mais antigos aparecem primeiro
        return linhas

    def filter_update(self, event=None):
        if self.status['updating_logs']:        # evita que duas atualizações se iniciem ao mesmo tempo
            return 0
        else:
            self.status['updating_logs'] = True

        linhas = self.get_log_data_lines()
        if (linhas):
            remover=[]              # rotina que atualiza informações do filtro
            if (self.cb1.GetValue() == False):
                for item in linhas:
                    if ('<' in item):
                        remover.append(item)
                for item in remover:
                    linhas.remove(item)
            self.logpanel.SetValue(''.join(linhas))

        self.status['updating_logs'] = False        # libera o sistema para uma nova atualização

    def update_logs(self, event=None):
        """Atualiza o painel de logs"""
        linhas = self.get_log_data_lines()
        panel_text = self.logpanel.GetValue()
        if linhas:
            if "Ainda não existe" in panel_text:            # Se estiver com o texto inicial apaga o painel antes de acrescentar as infos
                self.logpanel.Clear()
            for linha in linhas:
                if linha not in panel_text:
                    self.logpanel.AppendText(linha)
      
if __name__ == '__main__':
    
    '''Carregando informações do diretório raiz do projeto'''
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    

    status = {
        'sincronizando' : False,
        'evento_acontecendo' : False,
        'updating_logs' : False
    }
    zabbix_metric = [0]
    
    from LibFileLogger import FileLogger_
    logger_ = FileLogger_('logs')
    
    app = wx.App()  
 
    MyFrame_ = MyFrame(status, logger_, zabbix_metric, configs)
    app.MainLoop()