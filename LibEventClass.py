from watchdog.events import LoggingEventHandler
from LibFileLogger import FileLogger_
from LibFileOperations import FileOperations_
import os

class Event(LoggingEventHandler):
    def __init__(self, mylogger: FileLogger_, configs: str, fileoperations: FileOperations_):
        super().__init__()
        self.my_logger = mylogger
        self.configs = configs
        self.fileoperations = fileoperations

    def dispatch(self, event):
        
        self.my_logger.adiciona_linha_log(str(event))
        path_event = str(event.src_path)
        filenamesize = len(os.path.basename(path_event))
        sliceposition = len(path_event)- (filenamesize)
        path_event_dir = os.path.join(path_event[0:sliceposition],'')
        for sync in self.configs['folders_to_sync']:
            paths = [0,0]
            paths[0] = self.configs['folders_to_sync'][sync]['origem']
            paths[1] = self.configs['folders_to_sync'][sync]['destino']
            
            if os.path.join(paths[0], '') == path_event_dir:
                self.fileoperations.event_operations(path_event, paths[1], sync, event)
    

        
  