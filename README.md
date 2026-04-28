# Braiins Ratchet

Monitor-only research scaffold for optimizing a manual "buy hashpower on Braiins, mine through OCEAN" strategy.

The current implementation is monitor-only by design:

- The code never places, modifies, or cancels Braiins orders.
- The default strategy emits recommendations only.
- The strategy distinguishes `manual_canary` research experiments from `manual_bid` profit-seeking opportunities.
- The Braiins integration accepts a watcher-only token only.
- All mutable runtime state stays inside this repository under `data/`.
- The Git branch is `master`.
- The lifecycle engine uses Python standard library only; the native Mac app is SwiftUI.

## Quick Start

```bash
./scripts/ratchet app
```

This rebuilds the native macOS control room, replaces any stale app window, and opens the fresh bundle. Use the app for normal operation; terminal commands are advanced fallback tools.

The lifecycle state persists in `data/ratchet.sqlite`. If the app or Mac restarts, open the app again and it reads the same state.

Inside the app, the preferred non-babysitting path is `Start Forever Engine`. It starts the monitor-only lifecycle engine in the background, writes logs under `logs/`, persists state under `data/`, and never places Braiins orders.

When you manually place a Braiins bid, record the exposure so the supervisor blocks new experiments:

```bash
./scripts/ratchet position open --description "Braiins order abc" --maturity-hours 72
```

Close it only when finished:

```bash
./scripts/ratchet position close POSITION_ID
```

For the native macOS app:

```bash
./scripts/ratchet app
```

This builds `macos/build/Braiins Ratchet.app`, closes any stale `BraiinsRatchetMac` UI process, and opens the real app bundle. Do not use `swift run` for normal operation.

The app is a native Tahoe Flight Deck: animated hashfield background, real SwiftUI Liquid Glass controls, Hashflow, Ratchet, Bid Lab, Exposure, and Evidence. The design rationale is in `docs/APP_DESIGN_RESEARCH.md`.

Advanced fallback for a 6-hour CLI monitoring session:

```bash
./scripts/ratchet watch 6
```

Advanced fallback for the background monitor engine:

```bash
./scripts/ratchet engine status
./scripts/ratchet engine start
./scripts/ratchet engine stop
```

Every completed watch is now treated as a ratchet experiment. It writes a run report under `reports/run-*.md` and appends the master ledger at `reports/EXPERIMENT_LOG.md`.

To inspect the experiment ledger:

```bash
./scripts/ratchet experiments
```

To embed an already completed manual session from stored snapshots:

```bash
./scripts/ratchet retro 2026-04-25T19:08:00+00:00 2026-04-25T21:05:00+00:00
```

For the noob-friendly user guide:

```bash
./scripts/ratchet guide
```

For the operator installation, migration, recovery, and architecture handbook:

```bash
./scripts/ratchet operator-guide
```

Import a manual Braiins market snapshot:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli import-market examples/market_snapshot.example.json
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli evaluate
```

The JSON shape is:

```json
{
  "timestamp_utc": "2026-04-25T12:00:00+00:00",
  "best_price_btc_per_eh_day": "0.30",
  "available_hashrate_eh_s": "0.10",
  "source": "manual"
}
```

## Public Braiins Market Data

The collector first uses unauthenticated public web endpoints from `hashpower.braiins.com`; no token is needed for live price action. See `docs/BRAIINS_PUBLIC_MARKET.md`.

Watcher-only tokens are only relevant if we later need account-specific read-only data such as your private balance, historical fills, or order status. Owner tokens remain out of scope.

## Recommendation States

- `observe`: do nothing.
- `manual_canary`: a tiny manually executed research experiment is within the configured loss budget.
- `manual_bid`: a manually executed bid clears profit-seeking discount and risk guardrails.

The Braiins market report distinguishes visible top-of-book from executable depth:

- `best_ask_btc_per_eh_day`: cheapest visible ask.
- `fillable_price_btc_per_eh_day`: cheapest ask level with enough unmatched supply for the configured canary-sized target PH/s.
- `suggested_bid_btc_per_eh_day`: fillable price plus the configured overpay cushion.

## Documentation

- `PROGRAM.md`: research charter and ratchet rules.
- `START_HERE.md`: no-prior-knowledge operating instructions.
- `docs/USER_GUIDE.md`: app-first noob guide for the complete autoresearch loop.
- `docs/OPERATOR_GUIDE.md`: architecture, installation, migration, backup, recovery, and diagnostics.
- `SECURITY.md`: token, computer, and trading safety guardrails.
- `docs/BRAIINS_PUBLIC_MARKET.md`: public market collector behavior.
- `docs/RATCHET_OPERATIONS.md`: day-to-day monitor cycle.
- `docs/CLI_REFERENCE.md`: command reference and test command.
- `reports/EXPERIMENT_LOG.md`: master ratchet ledger with run-level hypotheses, outcomes, and adaptations.

## Tests

```bash
PYTHONPATH=src ./.venv/bin/python -m unittest discover -s tests
```

The tests are network-free and use fixtures for public Braiins parsing. Live collectors are intentionally separate operational checks.

## Guardrail Model

`braiins_ratchet.strategy` can propose a manual bid, but `braiins_ratchet.guardrails` decides whether that proposal is admissible. The executor layer currently has no write-capable Braiins methods. If live execution is ever added, it must be a separate reviewed change and remain disabled by default.

## Data Maturity

OCEAN's TIDES payout model means a canary experiment should not be scored immediately after spend completion. A spend should be treated as immature until its shares have had time to age through the pool's share-log window. The strategy therefore records both expected value and maturity notes.
