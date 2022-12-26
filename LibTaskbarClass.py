import wx.adv
import os
#import parse_config
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
task_icon = os.path.join(ROOT_DIR, 'task_icon.png')
#configuration = parse_config.ConfPacket()
#configs = configuration.load_config('SYNC_FOLDERS, SYNC_TIMES, SYNC_EXTENSIONS, ZABBIX, SYNC_NAME')


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, configs):
        self.frame = frame
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
        self.create_menu_item(menu, 'Abrir log', self.on_left_down)
        menu.AppendSeparator()
        self.create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, self.TRAY_TOOLTIP)

    def on_left_down(self, event):      
        self.frame.Show()
        
    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()
