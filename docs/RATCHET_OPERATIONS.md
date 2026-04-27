# Ratchet Operations

## Normal Monitor Cycle

Run these commands from the repository root:

```bash
./scripts/ratchet
```

This prints the cockpit and tells you exactly what to do next.

The cockpit also prints `Ratchet Pathway Forecast`. That section is the stretched-out research path:

- Immediate: the next operational step.
- Midterm: the likely next experiment stage.
- Longterm: what could happen after multiple reports mature.

Those probabilities are workload and workflow estimates, not promises of mining profit.

If the cockpit tells you to collect one fresh sample, run:

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

At the end of a normal watch, inspect the ratchet record:

```bash
./scripts/ratchet experiments
```

The ledger is the main artifact. It says what was tested, how long it ran, what actions the strategy would have considered, and what adaptation should be considered next.

After a completed watch, the cockpit should not immediately recommend another identical watch. It enters post-watch cooldown, which means the current stage is complete and the next useful operator touch is a later fresh sample.

During cooldown, the cockpit prints a progress bar, remaining minutes, and the earliest next action time. To let the app wait and perform the next monitor-only refresh after explicit approval, run:

```bash
./scripts/ratchet pipeline
```

The pipeline prints its plan and asks for `yes` or `no` before doing anything. It never places Braiins orders.

## Forever Lifecycle

For unattended monitor-only autoresearch:

```bash
./scripts/ratchet supervise
```

The supervisor is stateful. It writes lifecycle state and events into `data/ratchet.sqlite`, so a restart can continue from the current phase instead of starting over.

Check the persisted lifecycle state:

```bash
./scripts/ratchet supervise --status
```

This is still monitor-only. Manual Braiins bids remain outside the app unless separately recorded.

## Manual Exposure Tracking

When you manually place a Braiins order, record it:

```bash
./scripts/ratchet position open --description "Braiins order abc" --maturity-hours 72
```

The supervisor then blocks new experiments while the position is active. This is the stateful bridge for real-money operations that can run for days or weeks.

Close it only when the exposure is truly finished:

```bash
./scripts/ratchet position close POSITION_ID
```

If a run already happened before automatic bookkeeping was available, reconstruct it from the stored SQLite snapshots:

```bash
./scripts/ratchet retro 2026-04-25T19:08:00+00:00 2026-04-25T21:05:00+00:00
```

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
