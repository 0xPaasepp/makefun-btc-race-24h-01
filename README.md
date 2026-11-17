# btc-race-24h — dip-buy mean-reversion bot

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/0xPaasepp/makefun-btc-race-24h-01/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/0xPaasepp/makefun-btc-race-24h-01/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A pure-stdlib Python trading bot for make.fun's [Race a BTC trading bot live for 24 hours](https://make.fun/bounty/btc-race-24h-20261117-0603) bounty ($250 in USDC).

## Strategy

Dip-buy mean reversion on cbBTC 1-minute bars: buy when the close is 80 bps below the 60-bar SMA, exit at +150 bps take-profit, -70 bps stop-loss, or 720-bar max hold. After a stop-loss the cooldown is 10 bars and the first re-entry needs a rising close (unless the dislocation is 120 bps or deeper, or 120 bars have passed); after a take-profit or max-hold exit the cooldown is 30 bars. Late-window fallbacks guarantee at least one trade.

## Results (frozen dev window, 1,440 bars)

- Net PnL +$28.99 (+2.90%), max drawdown 0.76%, 4 trades, fees $1.62
- Buy-and-hold on the same window: +$1.07; kit RSI-Bollinger baseline: -$24.25

## Run

```
python3 main.py
```
