"""
Reader/Writer locks.  An RW lock allows concurrent access for read-only operations, 
whereas write operations require exclusive access.
"""

__all__ = ["RWLock"]

import time
from types import TracebackType
from typing import Callable, Optional, Type
from typing_extensions import runtime_checkable, Protocol
import threading

try:
    threading.Lock().release()
except BaseException as exc:
    RELEASE_ERR_CLS = type(exc)
    RELEASE_ERR_MSG = str(exc)
else:
    raise AssertionError()


@runtime_checkable
class Lockable(Protocol):
    """Lockable interface."""

    def acquire(self, blocking=True) -> bool:
        raise AssertionError("Should be overridden")
    
    def release(self) -> None:
        raise AssertionError("Should be overridden")
    
    def locked(self) -> bool:
        raise AssertionError("Should be overridden")
    
    def __enter__(self) -> bool:
        """Enter context manager."""
        self.acquire()
        return False
    
    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val:Optional[Exception], 
                 exc_tb: Optional[TracebackType]) -> Optional[bool]:
        """Exit context manager."""
        self.release()
        return False  

@runtime_checkable
class RWLockable(Protocol):
    """Read/Write lock."""

    def gen_rlock(self) -> Lockable:
        """Generate a reader lock"""
        raise AssertionError("Should be overridden")
    
    def gen_wlock(self) -> Lockable:
        """Generate a writer lock"""
        raise AssertionError("Should be overridden")
    

class RWLock(RWLockable):
    """
    A Read/Write lock giving preference to Reader.
    The interface is compatible with threading.Lock().
    You can refer https://en.wikipedia.org/wiki/Readers%E2%80%93writer_lock#Using_two_mutexes
    for implementation.
    """
    def __init__(self, lock_factory:Callable[[], Lockable]=threading.Lock):
        self.read_cnt:int = 0
        self.resource_lock = lock_factory()
        self.read_cnt_lock = lock_factory()

    class _rlock(Lockable):
        def __init__(self, p_RWLock: "RWLock") -> None:
            self.rw_lock = p_RWLock
            self.locked = False

        def acquire(self, blocking=True) -> bool:
            if not self.rw_lock.read_cnt_lock.acquire(blocking):
                return False
            self.rw_lock.read_cnt += 1
            if 1 == self.rw_lock.read_cnt:
                if not self.rw_lock.resource_lock.acquire(blocking):
                    self.rw_lock.read_cnt -= 1
                    self.rw_lock.read_cnt_lock.release()
                    return False
            self.rw_lock.read_cnt_lock.release()
            self.locked = True
            return True
        
        def release(self) -> None:
            if not self.locked:
                raise RELEASE_ERR_CLS(RELEASE_ERR_MSG)
            self.locked = False
            self.rw_lock.read_cnt_lock.acquire()
            self.rw_lock.read_cnt -= 1
            if 0 == self.rw_lock.read_cnt:
                self.rw_lock.resource_lock.release()
            self.rw_lock.read_cnt_lock.release()                   

        def locked(self) -> bool:
            return self.locked

    class _wlock(Lockable):
        def __init__(self, p_RWLock: "RWLock") -> None:
            self.rw_lock = p_RWLock
            self.locked = False

        def acquire(self, blocking=True) -> bool:
            if not self.rw_lock.resource_lock.acquire(blocking):
                return False
            self.locked = True
            return True
        
        def release(self) -> None:
            if not self.locked:
                raise RELEASE_ERR_CLS(RELEASE_ERR_MSG)
            self.locked = False
            self.rw_lock.resource_lock.release()

        def locked(self) -> bool:
            return False

    def gen_rlock(self) -> "RWLock._rlock":
        return RWLock._rlock(self)
    
    def gen_wlock(self) -> "RWLock._wlock":
        return RWLock._wlock(self)

import random   
if __name__ == '__main__':
    store = []
    rw_lock = RWLock()
    write_finished = False
    write_elem = 0
    
    def read_element(reader_id):
        r_lock = rw_lock.gen_rlock()
        progress = 0
        while True:            
            if progress < len(store):
                r_lock.acquire()
                print(f'{reader_id} get element {store[progress]}')
                progress += 1
                r_lock.release()
            else:
                if write_finished:
                    break
                #time.sleep(random.random())
    
    def write_element(writer_id):
        global write_elem 
        w_lock = rw_lock.gen_wlock()
        for i in range(5):
            w_lock.acquire()
            store.append(write_elem)
            print(f'{writer_id} write element {write_elem}')
            write_elem += 1
            w_lock.release()
            
    
    writers = []
    threading.Thread(target=read_element, args=(1,)).start()
    writers.append(threading.Thread(target=write_element, args=(1,)))
    writers[-1].start()
    threading.Thread(target=read_element, args=(2,)).start()
    writers.append(threading.Thread(target=write_element, args=(2,)))
    writers[-1].start()
    threading.Thread(target=read_element, args=(3,)).start()
    writers.append(threading.Thread(target=write_element, args=(3,)))
    writers[-1].start()
    threading.Thread(target=read_element, args=(4,)).start()
    
    for w in writers:
        w.join()
    
    write_finished = True


    


    



    



    

