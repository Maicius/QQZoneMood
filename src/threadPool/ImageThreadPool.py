import threading

class ImageThreadPool(object):
    def __init__(self, max_thread=20):
        self.queue = []
        for i in range(max_thread):
            self.queue.append(threading.Thread)

    def get_thread(self):
        while True:
            length = len(self.queue)
            if length > 0:
                return self.queue.pop(0)

    def add_thread(self):
        self.queue.append(threading.Thread)