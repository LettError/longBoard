#!/usr/bin/env python3

# ----- #
# Tools #
# ----- #

# -- Modules -- #
from collections import deque
from itertools import chain, repeat


# -- Functions -- #
def windowed(seq, n, fillvalue=None, step=1):
    # from https://github.com/more-itertools/more-itertools/blob/b469c17e2bb48d7b9aca11365e112736b8e814f6/more_itertools/more.py#L832
    """Return a sliding window of width *n* over the given iterable.
        >>> all_windows = windowed([1, 2, 3, 4, 5], 3)
        >>> list(all_windows)
        [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
    When the window is larger than the iterable, *fillvalue* is used in place
    of missing values:
        >>> list(windowed([1, 2, 3], 4))
        [(1, 2, 3, None)]
    Each window will advance in increments of *step*:
        >>> list(windowed([1, 2, 3, 4, 5, 6], 3, fillvalue='!', step=2))
        [(1, 2, 3), (3, 4, 5), (5, 6, '!')]
    To slide into the iterable's items, use :func:`chain` to add filler items
    to the left:
        >>> iterable = [1, 2, 3, 4]
        >>> n = 3
        >>> padding = [None] * (n - 1)
        >>> list(windowed(chain(padding, iterable), 3))
        [(None, None, 1), (None, 1, 2), (1, 2, 3), (2, 3, 4)]
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    if n == 0:
        yield tuple()
        return
    if step < 1:
        raise ValueError("step must be >= 1")

    window = deque(maxlen=n)
    i = n
    for _ in map(window.append, seq):
        i -= 1
        if not i:
            i = step
            yield tuple(window)

    size = len(window)
    if size < n:
        yield tuple(chain(window, repeat(fillvalue, n - size)))
    elif 0 < i < min(step, n):
        window += (fillvalue,) * i
        yield tuple(window)
