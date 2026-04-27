# CLI Reference

Most users should use the wrapper:

```bash
./scripts/ratchet setup
./scripts/ratchet
```

`./scripts/ratchet` defaults to `./scripts/ratchet next`, the operator cockpit. It tells you exactly what to do next.

Use `./scripts/ratchet raw-cycle` only when debugging the machine-readable cycle output.

The raw Python CLI is documented below for debugging and development.

All raw commands should be run from the repository root.

Use the local virtual environment:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli <command>
```

## `next`

Prints the cockpit: current state, exact next operator action, interpretation, and reference commands.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli next
```

## `pipeline`

Prints a monitor-only automation proposal and asks for `yes` or `no`.

Example behavior during post-watch cooldown:

```text
I am going to: Wait for post-watch cooldown, then refresh once.
Are you OK with this? Type yes or no.
```

If approved, it waits until the earliest next action time, runs one fresh monitor cycle, prints the cockpit, and stops.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli pipeline
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

## `cycle`

Runs one complete monitor pass:

1. collect OCEAN
2. collect public Braiins market data
3. evaluate the strategy
4. store the resulting proposal

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli cycle
```

Use existing stored data for one side if needed:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli cycle --skip-ocean
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli cycle --skip-braiins
```

## `watch`

Runs a bounded monitor loop. The interval floor is 30 seconds to avoid hammering public endpoints.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli watch --cycles 12 --interval-seconds 300
```

On normal completion, this writes a run report under `reports/` and appends `reports/EXPERIMENT_LOG.md`.

## `experiments`

Prints the master ratchet ledger.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli experiments
```

## `retro-report`

Summarizes already stored snapshots from an earlier run. Use `--write` to create a report file and append the ledger.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli retro-report --since 2026-04-25T19:08:00+00:00 --until 2026-04-25T21:05:00+00:00 --run-id retro-second-watch --write
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

The command returns `observe`, `manual_canary`, or `manual_bid`. It never places an order.

## `report`

Prints the latest OCEAN snapshot, latest Braiins snapshot, sampled price range, and latest proposal.
The sampled price range uses public Braiins snapshots only, so manually imported examples do not skew operational statistics.

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli report
```

Control the number of recent market samples used for min/avg/max:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli report --samples 200
```

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
