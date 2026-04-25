# CLI Reference

All commands should be run from the repository root.

Use the local virtual environment:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli <command>
```

## `init-db`

Creates `data/ratchet.sqlite` if it does not exist.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli init-db
```

## `collect-ocean`

Fetches one OCEAN dashboard snapshot and stores:

- pool hashrate
- network difficulty
- share-log window
- estimated OCEAN block time

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli collect-ocean
```

## `collect-braiins-public`

Fetches one token-free Braiins public market snapshot and stores:

- best bid
- best ask
- last average price
- market status
- total hashrate
- available hashrate

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli collect-braiins-public
```

Override the public base URL only for testing:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli collect-braiins-public --base-url https://hashpower.braiins.com/webapi
```

## `import-market`

Imports a manual market JSON snapshot. Use this when public Braiins endpoints are unavailable.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli import-market examples/market_snapshot.example.json
```

## `evaluate`

Evaluates the latest stored OCEAN and Braiins snapshots against `config.example.toml`.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli evaluate
```

The command returns `observe` or `manual_bid`. It never places an order.

## `guardrails`

Prints the active guardrails.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli guardrails
```

## Tests

Run all tests:

```bash
PYTHONPATH=src ./.venv/bin/python -m unittest discover -s tests
```

The test suite is network-free. Live collectors are validated separately by explicitly running their commands.

