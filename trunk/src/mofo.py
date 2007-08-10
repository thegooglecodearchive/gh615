import threading, time

class TaskThread(threading.Thread):
    """Thread that executes a task every N seconds"""
    
    def __init__(self):
        threading.Thread.__init__(self)
        self._finished = threading.Event()
    
    def shutdown(self):
        """Stop this thread"""
        self._finished.set()
    
    def run(self):
        while 1:
            if self._finished.isSet(): return
            self.task()
            
            # sleep for interval or until shutdown
            self._finished.wait(2.0)
    
    def task(self):
        """The task done by this thread - override in subclasses"""
        #pass

class gh615Thread(TaskThread):      
    parentInit = TaskThread.__init__
        
    def __init__(self, gh615, method, *args):
        self.gh615 = gh615
        self.method = method
        self.args = args
        self.parentInit()

    def task(self):        
        func = getattr(self.gh615, self.method)
        if callable(func):            
            if func(*self.args) == 1:
                print 'shuting down'
                self.shutdown()
        else:
            print 'not found'