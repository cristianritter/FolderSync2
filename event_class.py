from watchdog.events import LoggingEventHandler
from FileLogger import FileLogger_
from FileOperations import FileOperations_
import os

class Event(LoggingEventHandler):
    def __init__(self, logger=None, mylogger=None, configs=None, fileoperations=None):
        super().__init__(logger)
        self.my_logger = mylogger
        self.configs = configs
        self.fileoperations = fileoperations

    def dispatch(self, event):
        assert isinstance(self.my_logger, FileLogger_)
        assert isinstance(self.fileoperations, FileOperations_)
        
        LoggingEventHandler()
        self.my_logger.adiciona_linha_log(str(event))
        print(event)
        path_event = str(event.src_path)
        filenamesize = (len(self.fileoperations.getfilename(path_event)))
        sliceposition = len(path_event)- (filenamesize)
        path_event_dir = os.path.join(path_event[0:sliceposition],'')
        for sync in self.configs['SYNC_FOLDERS']:
            paths = (self.configs['SYNC_FOLDERS'][sync]).split(', ')
            if os.path.join(paths[0], '') == path_event_dir:
                pass
                self.fileoperations.event_operations(path_event, paths[1], sync, event)
    

        
  