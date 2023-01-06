import wx
import os
from datetime import datetime
import locale
from LibFileLogger import FileLogger_

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
task_icon = os.path.join(ROOT_DIR, 'task_icon.png')

def InitLocale(self):
    """    Substituição do método padrão devido a problemas relacionados a detecção de locale no Windows 7. """
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
        ld1txt = wx.StaticText(panel, label='Event operation in progress')
        self.led2 =  wx.StaticText(panel, wx.ID_ANY, "", size=(20,15))
        ld2txt = wx.StaticText(panel, label='Timed Sync in progress')
        #self.led3 =  wx.StaticText(panel, wx.ID_ANY, "", size=(20,15))
        #ld3txt = wx.StaticText(panel, label='Error detected')

        self.logpanel = wx.TextCtrl(panel, value='', style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2, size=(-1,-1))
        #self.clear_btn = wx.StaticText(panel, label='(Limpar Erros)')
        self.cb1 = wx.CheckBox(panel, label='Visualização completa com descrição de eventos')
        self.cb1.SetValue(True)
        self.searchbox = wx.SearchCtrl(panel, style=wx.TE_PROCESS_ENTER, value='')
        """Configuração de Fonts"""
        TittleFont = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        StaticTextTittle.SetFont(TittleFont)
        ButtonFont = wx.Font(7, wx.DEFAULT, wx.FONTSTYLE_ITALIC, wx.BOLD, underline=True)
        #self.clear_btn.SetFont(ButtonFont)

        """Configuração de Items Colors"""    
        self.led1.SetBackgroundColour('gray')
        self.led2.SetBackgroundColour('gray')
        #self.led3.SetBackgroundColour('gray')

        """Items Binds"""
        #self.clear_btn.Bind(wx.EVT_LEFT_DOWN, self.clear_error_led)
        self.cb1.Bind(wx.EVT_CHECKBOX, self.on_checkbox_change)
        self.searchbox.Bind(wx.EVT_TEXT_ENTER, self.searchevent)
        self.searchbox.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.searchevent)
        
        self.Bind(wx.EVT_CLOSE, self.on_hide)
        self.delay_update_panel = wx.CallLater(300, self.panel_update)
        self.delay_update_panel.Stop()

        """Organização dos items [containers]"""
        linha_titulo = wx.BoxSizer(wx.HORIZONTAL)
        linha_titulo.Add(StaticTextTittle, 0, wx.ALL, border=5)
        linha_filter = wx.BoxSizer(wx.HORIZONTAL)
        linha_filter.Add(self.searchbox, 0, wx.ALL, 5)
        linha_filter.AddSpacer(30)
        linha_filter.Add(self.cb1, 0, wx.TOP, 8)
        linha_led = wx.BoxSizer(wx.HORIZONTAL)
        linha_led.Add(self.led1, 0, wx.ALL, border=5)
        linha_led.Add(ld1txt, 0, wx.ALL, border=5)
        linha_led.AddSpacer(20)
        linha_led.Add(self.led2, 0, wx.ALL, border=5)
        linha_led.Add(ld2txt, 0, wx.ALL, border=5)
        linha_led.AddSpacer(20)
        #linha_led.Add(self.led3, 0, wx.ALL, border=5)
        #linha_led.Add(ld3txt, 0, wx.ALL, border=5)
        linha_led.AddSpacer(20)
        #linha_led.Add(self.clear_btn, 0, wx.ALL, border=5)
        
        coluna_todo_conteudo = wx.BoxSizer(wx.VERTICAL) 
        coluna_todo_conteudo.Add(linha_titulo, 0, wx.CENTER | wx.ALL, border=10)
        coluna_todo_conteudo.Add(self.logpanel, 1, wx.ALL | wx.EXPAND, 5) 
        coluna_todo_conteudo.Add(linha_filter, 0, wx.ALIGN_CENTER | wx.ALL, border=10) 
        coluna_todo_conteudo.Add(linha_led, 0, wx.CENTER | wx.ALL, border=20) 
       
        panel.SetSizer(coluna_todo_conteudo)
        self.Center()
        self.Show()

    def searchevent(self, event):
        self.logpanel.Clear()
        self.panel_update()
        self.searchbox.Clear()
    
    def on_checkbox_change(self, event=None):
        self.logpanel.Clear()                               # Limpa o painel caso o checkbox seja acionado
        if not self.delay_update_panel.IsRunning():                               # if delay timer does not run, start it, either restart it
            self.delay_update_panel.Start(300)
        else:
            self.delay_update_panel.Restart(300)

    def on_hide(self, event):
        """Método que oculta a janela do programa para a bandeja do sistema"""
        self.Hide()

    def set_led1_red(self, event=None):
        """Método que troca a cor do sinalizador de evento em curso para vermelho"""
        self.led1.SetBackgroundColour('Red')
        self.Refresh()

    def set_led1_orange(self, event=None):
        """Método que troca a cor do sinalizador de evento em curso para amarelo """
        self.led1.SetBackgroundColour('Yellow')
        self.Refresh()

    def set_led1_cinza(self, event=None):
        """Método que troca a cor do sinalizador de evento em curso para cinza"""
        self.led1.SetBackgroundColour('gray')
        self.Refresh()

    def set_led2_red(self, event=None):
        """Método que troca a cor do sinalizador de sincronismo em curso para vermelho"""
        self.led2.SetBackgroundColour('Red')
        self.Refresh()

    def set_led2_orange(self, event=None):
        """Método que troca a cor do sinalizador de sincronismo em curso para amarelo"""
        self.led2.SetBackgroundColour('Yellow')
        self.Refresh()

    def set_led2_cinza(self, event=None):
        """Método que troca a cor do sinalizador de sincronismo em curso para cinza"""
        self.led2.SetBackgroundColour('gray')
        self.Refresh()

    #def set_error_led(self, event=None):
    #    """Método que troca a cor do sinalizador de erro ocorrido para vermelho"""
    #    self.led3.SetBackgroundColour('Red')
    #    self.Refresh()

    #def clear_error_led(self, event=None):
    #    """Método que troca a cor do sinalizador de erro ocorrido para cinza"""
    #    self.led3.SetBackgroundColour('gray')
    #    self.Refresh()

    def get_log_data_lines(self):
        dataPartialLogFname = datetime.now().strftime('_%Y%m')
        logFilename = f'log{dataPartialLogFname}.txt'     
        log_pathfile = os.path.join(ROOT_DIR, 'logs', logFilename)
        if not os.path.exists(log_pathfile):            #sai da função se o arquivo nao existir por alguma razão
            return 0
        with open(log_pathfile, "r") as file:
            linhas = file.readlines(20000000)
        #linhas.reverse()        #reverse pois os logs mais antigos aparecem primeiro
        return linhas

    def panel_update(self, event=None):
        """Atualiza o painel de logs"""
        empty_panel_string = "Não há nada aqui por enquanto..."
        lines_from_file = self.get_log_data_lines()         # Captura informação do arquivo
        lines_from_panel = self.logpanel.GetValue()         # Captura informação do painel
        if lines_from_file:                             # Se houver informação no arquivo
            if empty_panel_string in lines_from_panel:
                self.logpanel.Clear()
            for linha in lines_from_file:
                if (self.cb1.GetValue() == False):      # Filtra linhas com a palavra 'Event'
                    if ('Event' in linha):
                        continue
                if (self.searchbox.GetValue()!="" and self.searchbox.GetValue().lower() in linha.lower()):
                    self.logpanel.SetDefaultStyle(wx.TextAttr(wx.WHITE, wx.BLACK))
                elif ('erro' in linha.lower() or 'corrompida' in linha.lower()):
                    self.logpanel.SetDefaultStyle(wx.TextAttr(wx.RED, wx.BLACK))
                else:
                    self.logpanel.SetDefaultStyle(wx.TextAttr(wx.BLACK, wx.WHITE))
               
                if linha not in lines_from_panel:       # Adiciona as linhas não filtradas
                    self.logpanel.AppendText(f'{linha}')
        elif not lines_from_panel:
            self.logpanel.AppendText(empty_panel_string)        # Se não houver informações no arquivo
      
if __name__ == '__main__':
    
    '''Carregando informações do diretório raiz do projeto'''
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    

    status = {
        'sincronizando' : False,
        'evento_acontecendo' : False
    }
    zabbix_metric = [0]
    
    from LibFileLogger import FileLogger_
    logger_ = FileLogger_('logs')
    
    app = wx.App()  
 
    MyFrame_ = MyFrame(status, logger_, zabbix_metric, configs)
    app.MainLoop()