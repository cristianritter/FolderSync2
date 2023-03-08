import wx
import wx.adv
import os
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
#task_icon = os.path.join(ROOT_DIR, 'public/ico_large.png')
task_icon = '.\public\ico_large.png'


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, configs):
        self.frame = frame
        self.configs = configs
        super(TaskBarIcon, self).__init__()
        self.TRAY_TOOLTIP = 'FolderSync - ' + configs['trayicon_alias']
        self.set_icon(task_icon)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def create_menu_item(self, menu, label, func):
            item = wx.MenuItem(menu, -1, label)
            menu.Bind(wx.EVT_MENU, func, id=item.GetId())
            menu.Append(item)
            return item

    def CreatePopupMenu(self):
        menu = wx.Menu()
        self.create_menu_item(menu, f"View {self.configs['trayicon_alias']} ", self.on_left_down)
        menu.AppendSeparator()
        self.create_menu_item(menu, f"About", self.on_infos)
        self.create_menu_item(menu, f"Exit Application", self.on_exit)
        return menu

    def on_infos(self, event):
        """Mostra informações sobre o desenvolvedor e o app."""
        description = f"""'FolderSync' é um aplicativo para sincronismo de pastas 
que monitora mudanças em diretórios pré configurados
e espelha o seu conteúdo em uma pasta de destino.  
"""
        licence = f"""Contrato de Licença de Software - Foldersync
POR FAVOR LEIA ESTE ACORDO CUIDADOSAMENTE. AO COPIAR, 
INSTALAR OU USAR TODO OU PARTE DESTE SOFTWARE, VOCÊ 
(doravante "CLIENTE") ACEITA TODOS OS TERMOS E CONDIÇÕES
DE USO DESTE PRODUTO, INCLUINDO, SEM LIMITAÇÃO, AS DISPOSIÇÕES
SOBRE RESTRIÇÕES DE LICENÇA, GARANTIA LIMITADA, LIMITAÇÃO DE 
RESPONSABILIDADE E DISPOSIÇÕES E EXCEÇÕES ESPECÍFICAS. 
O CLIENTE CONCORDA QUE ESTE CONTRATO É COMO QUALQUER CONTRATO 
NEGOCIADO ESCRITO E ASSINADO PELO CLIENTE. ESTE CONTRATO É 
EXECUTIVO CONTRA O CLIENTE. SE O CLIENTE NÃO CONCORDAR COM OS
TERMOS DESTE CONTRATO, O CLIENTE NÃO PODERÁ USAR O SOFTWARE.

"""

        info = wx.adv.AboutDialogInfo()

        info.SetIcon(wx.Icon('about_icon.png', wx.BITMAP_TYPE_PNG))
        info.SetName('FolderSync')
        info.SetVersion("1.2")
        info.SetDescription(description)
        info.SetCopyright("Cristian Ritter 2023")
        info.SetWebSite('cristianritter@gmail.com')
        info.SetLicence(licence)
        info.AddDeveloper('Cristian Ritter')
     
        wx.adv.AboutBox(info)
    
    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, self.TRAY_TOOLTIP)

    def on_left_down(self, event):      
        self.frame.Show()
        
    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Destroy()
