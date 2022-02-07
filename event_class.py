import os
import parse_config
from watchdog.events import LoggingEventHandler


ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
configuration = parse_config.ConfPacket()
configs = configuration.load_config('SYNC_FOLDERS, SYNC_TIMES, SYNC_EXTENSIONS, ZABBIX, SYNC_NAME')


class Event(LoggingEventHandler):
    """def dispatch(self, event): 
        LoggingEventHandler()
        #adiciona_linha_log(str(event))
        print(event)
        path_event = str(event.src_path)
        filenamesize = (len(self.getfilename(path_event)))
        sliceposition = len(path_event)- (filenamesize)
        path_event_dir = os.path.join(path_event[0:sliceposition],'')
        for sync in configs['SYNC_FOLDERS']:
            paths = (configs['SYNC_FOLDERS'][sync]).split(', ')
            if os.path.join(paths[0], '') == path_event_dir:
                pass
                #event_operations(path_event, paths[1], sync, event)
    """
    def getfilename(self, filepath):
        try:
            pathlist = filepath.split('\\')
            filename = (pathlist[len(pathlist)-1]).lower()
            return (filename)
        except Exception as Err:
            pass
            #adiciona_linha_log(str(Err)+'Getfilename')

        
  #  except Exception as err:
  #      adiciona_linha_log("Logging event handler erro - "+str(err))
