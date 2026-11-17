"""Dip-buy mean-reversion bot for agent-fun/bars-replay/v1 (make.fun btc-race-24h).

Strategy, in one line: buy cbBTC only when its close is far below its 60-bar
mean, sell when it has recovered, and never chase a rally.

The hello message gives the universe (one symbol, CBBTC), the capital
(1,000 USDC), the caps (long only, one open position, 16 orders per bar) and
the fees (4 bps fee, 2 bps slippage, plus constant-product impact against the
bar's pool depth). Each batch carries one 1-minute bar and the account; every
reply answers exactly one batch with its orders, echoing its seq. An order
decided on the batch of the bar that closes at minute t fills at the open of
the next bar, so every decision here uses only closes already seen.

Why this shape: on this pool the 1-minute noise is tiny (about 6 bps) while a
full-size round trip costs about 35 bps in fee, slippage and impact, so a
trade must catch a real dislocation. Dips of 80 bps or more below the 60-bar
mean are rare and they snap back; rallies, by contrast, are bought late and
sold into the same costs, so this bot never buys strength while a dip is on
offer. A trailing stop was tested on the dev window and added nothing over a
fixed take-profit, so the exits stay simple: take-profit, stop-loss, or a
maximum hold time. The bot holds at most one position and buys with all of
its cash.

Risk controls: at most one open position; a 70 bps stop-loss against the
average entry price; a 30-bar cooldown after every exit so one bad read cannot
re-enter at once. The hold time is counted from the first batch on which the
position is actually held, not from the batch the buy was sent on, so a fill
that lands a bar later cannot shorten it.

Late-window fallbacks (they only ever fire when the bot has not traded at
all, so the entry always meets the race's minimum of one trade): from bar
1200 a shallower dip is enough, from bar 1350 any small dip is enough, and
from bar 1380 a clear uptrend is enough -- if the window rose smoothly for 23
hours with no dip at all, buying the trend for the last hour beats sitting
out. No randomness, no clock, no network, no files: two executions on the
same bars produce the same orders.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"

# --- tuned parameters (grid-searched on the frozen dev window) ---
SMA_BARS = 60            # mean window, in bars
DIP_BPS = 80             # buy when close is this far below the mean, in bps
TAKE_PROFIT_BPS = 150    # sell when close is this far above the entry price
STOP_LOSS_BPS = 70       # sell when close is this far below the entry price
MAX_HOLD_BARS = 720      # sell when the position is this old, whatever the price
COOLDOWN_BARS = 30       # bars to wait after an exit before buying again
MAX_SLIPPAGE_BPS = 300   # widest fill we accept, measured from the latest close
FALLBACK_BAR = 1200      # from here, accept a shallower dip if never traded
FALLBACK_DIP_BPS = 40
LAST_RESORT_BAR = 1350   # from here, accept any small dip if never traded
LAST_RESORT_DIP_BPS = 25
TREND_BAR = 1380         # from here, accept a clear uptrend if never traded
TREND_BPS = 50

BPS = 10_000


class Bot:
    """Keeps the bar history and the trade state across batches."""

    def __init__(self):
        self.closes = []
        self.entry_seq = -1
        self.cool_until = -1
        self.ever_traded = False

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0
        if qty > 0:
            self.ever_traded = True
            if self.entry_seq < 0:
                self.entry_seq = state.seq
        if len(self.closes) < SMA_BARS:
            return []
        mean = sum(self.closes[-SMA_BARS:]) // SMA_BARS
        seq = state.seq

        if qty > 0:
            # Average entry price from the position's cost (fees included, so
            # this is a touch above the fill price: conservative both ways).
            entry_px = holding.cost * 10 ** 13 // (qty * 10 ** 6)
            move_bps = (close - entry_px) * BPS // entry_px
            if (
                move_bps >= TAKE_PROFIT_BPS
                or move_bps <= -STOP_LOSS_BPS
                or seq - self.entry_seq >= MAX_HOLD_BARS
            ):
                self.cool_until = seq + COOLDOWN_BARS
                self.entry_seq = -1
                return [
                    {
                        "side": "sell",
                        "symbol": SYMBOL,
                        "qty": qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }
                ]
            return []

        if seq < self.cool_until:
            return []
        dip_bps = (close - mean) * BPS // mean
        buy = dip_bps <= -DIP_BPS
        if not self.ever_traded and not buy:
            if seq >= TREND_BAR and dip_bps >= TREND_BPS:
                buy = True
            elif seq >= LAST_RESORT_BAR and dip_bps <= -LAST_RESORT_DIP_BPS:
                buy = True
            elif seq >= FALLBACK_BAR and dip_bps <= -FALLBACK_DIP_BPS:
                buy = True
        if buy and state.cash > 0:
            return [
                {
                    "side": "buy",
                    "symbol": SYMBOL,
                    "notional_quote_units": state.cash,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }
            ]
        return []


_BOT = Bot()


def on_batch(state, batch):
    return _BOT.on_batch(state, batch)


makefun_bars.run(on_batch)
