# Braiins Ratchet

Monitor-only research scaffold for optimizing a manual "buy hashpower on Braiins, mine through OCEAN" strategy.

The first implementation is deliberately conservative:

- The code never places, modifies, or cancels Braiins orders.
- The default strategy emits recommendations only.
- The Braiins integration accepts a watcher-only token only.
- All mutable runtime state stays inside this repository under `data/`.
- The Git branch is `master`.
- The project uses Python standard library only.

## Quick Start

```bash
./scripts/ratchet setup
./scripts/ratchet once
```

For a 6-hour monitoring session:

```bash
./scripts/ratchet watch 6
```

For the human operating guide:

```bash
./scripts/ratchet explain
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

## Documentation

- `PROGRAM.md`: research charter and ratchet rules.
- `SECURITY.md`: token, computer, and trading safety guardrails.
- `docs/BRAIINS_PUBLIC_MARKET.md`: public market collector behavior.
- `docs/RATCHET_OPERATIONS.md`: day-to-day monitor cycle.
- `docs/CLI_REFERENCE.md`: command reference and test command.

## Tests

```bash
PYTHONPATH=src ./.venv/bin/python -m unittest discover -s tests
```

The tests are network-free and use fixtures for public Braiins parsing. Live collectors are intentionally separate operational checks.

## Guardrail Model

`braiins_ratchet.strategy` can propose a manual bid, but `braiins_ratchet.guardrails` decides whether that proposal is admissible. The executor layer currently has no write-capable Braiins methods. If live execution is ever added, it must be a separate reviewed change and remain disabled by default.

## Data Maturity

OCEAN's TIDES payout model means a canary experiment should not be scored immediately after spend completion. A spend should be treated as immature until its shares have had time to age through the pool's share-log window. The strategy therefore records both expected value and maturity notes.
