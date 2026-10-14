"""Buggy block processors: a 3-tap FIR with carried history."""

import numpy as np

import dsp_props as dp


class MovingSum:
    """Reference: y[n] = x[n] + x[n-1] + x[n-2], processed block by block."""

    def __init__(self):
        self.hist = np.zeros(2)

    def process(self, block):
        buf = np.concatenate([self.hist, block])
        out = buf[2:] + buf[1:-1] + buf[:-2]
        self.hist = buf[-2:]
        return out


class StateResetEveryBlock(MovingSum):
    """History is not carried between blocks."""

    def process(self, block):
        self.hist = np.zeros(2)
        return super().process(block)


class HistoryOffByOne(MovingSum):
    """Keeps the wrong two samples as history."""

    def process(self, block):
        buf = np.concatenate([self.hist, block])
        out = buf[2:] + buf[1:-1] + buf[:-2]
        self.hist = buf[-3:-1] if len(buf) >= 3 else buf[-2:]
        return out


class EmptyBlockResetsState(MovingSum):
    """An empty block clobbers the state (the scipy#26406 pattern)."""

    def process(self, block):
        if len(block) == 0:
            self.hist = np.zeros(2)
        return super().process(block)


class ShortBlockPassthrough(MovingSum):
    """Blocks shorter than the filter are passed through unfiltered."""

    def process(self, block):
        if len(block) < 3:
            return np.asarray(block, dtype=float)
        return super().process(block)


MUTANTS = {
    "stream_state_reset_every_block": dp.streaming()(StateResetEveryBlock),
    "stream_history_off_by_one": dp.streaming()(HistoryOffByOne),
    "stream_empty_block_resets_state": dp.streaming()(EmptyBlockResetsState),
    "stream_short_block_passthrough": dp.streaming()(ShortBlockPassthrough),
}

REFERENCE = dp.streaming()(MovingSum)
