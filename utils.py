# -*- coding: utf-8 -*-
from functools import wraps
import time

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def stop_watch(func) :
    @wraps(func)
    def wrapper(*args, **kargs) :
        start = time.time()
        result = func(*args,**kargs)
        process_time =  (time.time() - start)*10000
        print("Processing time for {0}:{1:.3f}ms".format(func.__name__, process_time))
        return result
    return wrapper
