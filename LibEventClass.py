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
        for sync in self.configs['SYNC_FOLDERS']:
            paths = self.configs['SYNC_FOLDERS'][sync].split(', ')
            if os.path.join(paths[0], '') == path_event_dir:
                self.fileoperations.event_operations(path_event, paths[1], sync, event)
    

        
  