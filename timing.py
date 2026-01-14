import time
from contextlib import contextmanager


@contextmanager
def timed(label: str, sink=None):
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000

    if sink:
        sink({
            "type": "timing",
            "label": label,
            "ms": round(elapsed_ms, 3)
        })