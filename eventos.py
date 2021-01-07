from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import time

class Event(LoggingEventHandler):
    def dispatch(self, event): 
        LoggingEventHandler()
        print (str(event))
        if 'FileMovedEvent' in str(event):
            print(event.dest_path)
        time.sleep(1)

if __name__ == "__main__":
   
    event_handler = Event()
    observer = Observer()
    host = 'C:\\teste\\'
    observer.schedule(event_handler, host, recursive=False)
 
    observer.start()

    while 1:
        time.sleep(1)
