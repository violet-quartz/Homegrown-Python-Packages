"""
Timing tools for function calls, for Python 3.X only.

total(func, 1, 2, _reps=1000, a=3, b=4) calls func(1, 2, a=3, b=4)
 _reps times, and returns total time for all runs, with final result.

bestof(func, 1, 2, _reps=5, a=3, b=4) runs best-of-N timer attempt to
filter out system load variation, and returns best time among _reps tests.

bestoftotal(func, 1, 2, _reps1=5, _reps=1000, a=3, b=4) returns the best
among _reps1 runs of (the total of _reps runs).
"""

import time, sys

try:
    timer = time.perf_counter   # or time.process_time, new features since Python 3.3
except AttributeError:
    timer = time.clock if sys.platform[:3] =='win' else time.time

def total(func, *pargs, _reps=1000, **kwargs):
    start = timer()
    for _ in range(_reps):
        ret = func(*pargs, **kwargs)
    elapsed = timer() - start
    return (elapsed, ret)

def bestof(func, *pargs, _reps=5, **kwargs):
    best = float('inf')
    for _ in range(_reps):
        start = timer()
        ret = func(*pargs, **kwargs)
        elapsed = timer() - start
        best = min(elapsed, best)
    return (best, ret)

def bestoftotal(func, *pargs, _reps1=5, **kwargs):
    return min(total(func, *pargs, **kwargs) for _ in range(_reps1))

if __name__ == '__main__':
    print(total(pow, 2, 1000, _reps=10000)[0])
    print(bestof(pow, 2, 1000, _reps=10)[0])
    print(bestoftotal(pow, 2, 1000, _reps1=10, _reps=10000)[0])

