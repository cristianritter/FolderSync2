from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import time




class Event(LoggingEventHandler):
    def dispatch(self, event): 
        LoggingEventHandler()
        filepath = (str(event.src_path))
        pathlist = filepath.split('\\')
        filename = (pathlist[len(pathlist)-1])
        print(filename)
        time.sleep(1)
       


if __name__ == "__main__":
   
    event_handler = Event()
    observer = Observer()
    host = 'C:\\teste\\'
    host2 = 'C:\\teste2\\'
    host3 = 'C:\\teste3\\'
    observer.schedule(event_handler, host, recursive=False)
    observer.schedule(event_handler, host2, recursive=False)
    observer.schedule(event_handler, host3, recursive=False)

    observer.start()

    while 1:
        time.sleep(1)