import threading
import time

class ImageThreadPool(object):
    def __init__(self, max_thread=20):
        self.queue = []
        self.count = 0
        self.time_spend = 0
        for i in range(max_thread):
            self.queue.append(threading.Thread)

    def get_thread(self):
        begin_time = time.time() * 1000
        while True:
            length = len(self.queue)
            if length > 0:
                spend = int(time.time() * 1000 - begin_time)
                self.count += 1
                self.time_spend += spend
                return self.queue.pop(0)

    def add_thread(self):
        self.queue.append(threading.Thread)