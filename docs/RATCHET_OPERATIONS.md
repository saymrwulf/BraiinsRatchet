# Ratchet Operations

## Normal Monitor Cycle

Run these commands from the repository root:

```bash
./scripts/ratchet once
```

The result is a recommendation only. `observe` means no action is recommended. `manual_canary` means a tiny research experiment is inside the configured loss budget. `manual_bid` means a manually placed bid clears profit-seeking discount and risk guardrails.

The report's sampled price min/avg/max uses public Braiins snapshots only. Manual imports are still stored and can drive evaluation, but they do not pollute live market summary statistics.

The strategy price is depth-aware when orderbook depth is available: it prefers `suggested_bid_btc_per_eh_day` over raw best ask. This prevents top-of-book slivers or already-matched asks from looking cheaper than actually executable depth.

## Repeated Sampling

For short monitor sessions:

```bash
./scripts/ratchet watch 6
```

This runs for about six hours at 5-minute intervals. It is bounded by design.

## Manual Market Snapshot

If Braiins public endpoints are unavailable, use:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli import-market examples/market_snapshot.example.json
```

Edit a copy of the example JSON with values read from the Braiins UI. Do not put secrets in that file.

## Interpreting The Proposal

- `breakeven_btc_per_eh_day`: estimated expected mining value at current OCEAN/network inputs.
- `expected_reward_btc`: expected OCEAN reward before subtracting Braiins spend.
- `expected_net_btc`: expected reward minus Braiins spend.
- `score_btc`: risk-adjusted score after applying the configured penalty.
- `maturity_note`: how long to wait before treating a canary result as mature under the TIDES window.

## Safety

The program never places orders. Manual execution remains outside the repo and should use the Braiins UI, not this code.
