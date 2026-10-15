"""Subject 4: block FIR filtering by overlap-add, with the tail carried between blocks.

``OverlapAdd(h).process(block)`` returns as many samples as the block holds;
concatenating the outputs of successive blocks equals the one-shot FIR
output np.convolve(x, h)[:len(x)]. Mutated automatically.
"""

import numpy as np


class OverlapAdd:
    def __init__(self, h):
        self.h = np.asarray(h, dtype=float)
        self.tail = np.zeros(len(self.h) - 1)

    def process(self, block):
        block = np.asarray(block, dtype=float)
        n = len(block)
        taps = len(self.h)
        full = np.zeros(n + taps - 1)
        for i in range(n):
            full[i:i + taps] += block[i] * self.h
        full[:taps - 1] += self.tail
        self.tail = full[n:].copy()
        return full[:n].copy()
