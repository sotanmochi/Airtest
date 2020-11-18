import threading


class ThreadSafeIter:
    """
    Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()
        if getattr(self.it, "__next__") is None:  # for py2
            self.it.__next__ = self.it.next

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return self.it.__next__()

    def send(self, *args):
        with self.lock:
            return self.it.send(*args)

    next = __next__  # for Python 2


def threadsafe_generator(f):
    """
    A decorator that takes a generator function and makes it thread-safe.
    """
    def g(*a, **kw):
        return ThreadSafeIter(f(*a, **kw))
    return g
