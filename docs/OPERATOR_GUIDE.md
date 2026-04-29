# Braiins Ratchet Operator Guide

This handbook is for installing, operating, migrating, recovering, and auditing the whole Braiins Ratchet system.

The user guide is `docs/USER_GUIDE.md`. This file is lower-level and includes architecture, state ownership, host migration, and failure procedures.

## Operator Contract

The system is monitor-only.

It can:

1. Collect public Braiins market data.
2. Collect OCEAN dashboard data.
3. Store local snapshots.
4. Evaluate a shadow strategy.
5. Write run reports.
6. Start and stop a repo-local background monitor engine.
7. Track manual exposure entered by the user.

It cannot:

1. Place Braiins orders.
2. Modify Braiins orders.
3. Cancel Braiins orders.
4. Spend BTC.
5. Infer owner-token state that was not entered into the app.
6. Guarantee OCEAN block discovery.

Owner tokens must never be placed in this repository.

## System Architecture

### Tech Stack

The current stack is:

1. `SwiftUI` native macOS app in `macos/BraiinsRatchet`.
2. Swift tools `6.2` with `.macOS(.v26)`, targeting macOS Tahoe on Apple Silicon.
3. Python lifecycle and strategy engine in `src/braiins_ratchet`.
4. Python standard library only for runtime logic.
5. Repository-local Python virtual environment at `.venv`.
6. SQLite durable state at `data/ratchet.sqlite`.
7. Markdown evidence reports under `reports/`.
8. Bash launchers in `scripts/`.
9. SwiftUI self-reflection snapshots at `data/app_visual_state.md` and `data/app_visual_state.json`.
10. Git and GitHub on branch `master`.

### Runtime Layers

Layer 1 is the native app.

The app lives at `macos/BraiinsRatchet`. It presents the Flight Deck, Hashflow, Ratchet, Bid Lab, Exposure, and Evidence views. It calls the local script interface and displays structured state.

Layer 2 is the script boundary.

`./scripts/ratchet` is the stable operator entry point. It creates `.venv` if missing, sets `PYTHONPATH`, runs the Python CLI, builds the Mac app, and opens the packaged bundle.

Layer 3 is the Python CLI.

`src/braiins_ratchet/cli.py` exposes commands such as `app-state`, `cycle`, `watch`, `engine`, `position`, `report`, and `experiments`.

Layer 4 is durable state.

`src/braiins_ratchet/storage.py` owns SQLite tables for OCEAN snapshots, market snapshots, proposals, lifecycle state, lifecycle events, and manual positions.

Layer 5 is research evidence.

`src/braiins_ratchet/experiments.py` writes `reports/EXPERIMENT_LOG.md`, `reports/run-*.md`, and the active watch marker.

Layer 6 is the background engine.

`src/braiins_ratchet/engine.py` starts a detached monitor-only supervisor, writes `data/supervisor.pid`, and logs to `logs/supervisor.log`.

Layer 7 is the visual self-reflection layer.

The SwiftUI app renders a `Reality Mirror` HUD and tab. It writes the semantic state it believes it is showing to `data/app_visual_state.md` and `data/app_visual_state.json`. This is not screenshot OCR; it is the app's own rendered-state ledger.

During active watches, the backend exposes `active_watch_details` through `app-state`: run id, PID, start time, planned cycles, interval, elapsed seconds, remaining seconds, progress percent, next-cycle ETA, and estimated finish time. The SwiftUI Flight Deck renders this as a live progress panel and refreshes backend state roughly every 30 seconds.

### Data Flow

Normal data flow:

1. App asks for structured state with `./scripts/ratchet app-state`.
2. Python reads `data/ratchet.sqlite`.
3. Python computes current operator state and automation plan.
4. App renders the result graphically.
5. If the operator starts the engine, Python runs `supervise --yes` in the background.
6. The supervisor runs watch stages, records snapshots, writes reports, and enters cooldown.

One monitor cycle:

1. Fetch OCEAN snapshot.
2. Fetch public Braiins market snapshot.
3. Compute shadow proposal with `strategy.propose`.
4. Store proposal.
5. Return one of `observe`, `manual_canary`, or `manual_bid`.

### Durable Files

Critical files:

1. `data/ratchet.sqlite`: primary durable state.
2. `data/ratchet.sqlite-wal` and `data/ratchet.sqlite-shm`: possible SQLite WAL sidecar files.
3. `reports/EXPERIMENT_LOG.md`: master experiment ledger.
4. `reports/run-*.md`: run-level evidence.
5. `config.example.toml`: active default configuration unless a custom config is passed.

Operational files:

1. `data/supervisor.pid`: PID for the background engine.
2. `logs/supervisor.log`: background engine output.
3. `reports/ACTIVE_WATCH.json`: marker for a running watch.
4. `data/app_visual_state.md`: latest human-readable visual self-reflection snapshot.
5. `data/app_visual_state.json`: latest machine-readable visual self-reflection snapshot.
6. `.venv`: local Python environment, disposable.
7. `macos/build/Braiins Ratchet.app`: generated app bundle, disposable.

Source files:

1. `src/braiins_ratchet`: Python engine.
2. `macos/BraiinsRatchet`: native app source.
3. `scripts`: operator launchers.
4. `tests`: network-free test suite.

## Installation On A New Mac

Requirements:

1. macOS Tahoe.
2. Apple Silicon Mac.
3. Xcode or Xcode command-line tools with Swift 6.2 support.
4. Python 3.
5. Git.
6. Network access to GitHub, OCEAN, and public Braiins endpoints.

Fresh clone:

```bash
git clone -b master https://github.com/saymrwulf/BraiinsRatchet.git
cd BraiinsRatchet
```

Initialize local runtime:

```bash
./scripts/ratchet setup
```

Run tests:

```bash
./scripts/ratchet test
```

Build and open the app:

```bash
./scripts/ratchet app
```

First live sample:

```bash
./scripts/ratchet once
```

Preferred normal operation:

1. Open the app.
2. Use `Start Forever Engine`.
3. Leave the engine alone unless manual exposure needs to be recorded.

## Daily Operation

Normal app-first routine:

1. Start with `./scripts/ratchet app`.
2. Read `Flight Deck`.
3. If `ENGINE LIVE`, do nothing.
4. If `REFRESH`, run one fresh sample from the app.
5. If `WATCH`, start the forever engine or run one bounded watch.
6. If `COOLDOWN`, wait.
7. If `HOLD`, supervise manual exposure.
8. If `REVIEW`, inspect `Bid Lab` and `Evidence`.

Terminal fallback:

```bash
./scripts/ratchet
./scripts/ratchet once
./scripts/ratchet engine status
./scripts/ratchet engine start
./scripts/ratchet engine stop
./scripts/ratchet report
./scripts/ratchet experiments
```

Use terminal fallback only when the app cannot open or you are debugging.

## Autoresearch Lifecycle

The lifecycle is:

1. Sense.
2. Price.
3. Watch.
4. Mature.
5. Adapt.

`Sense` collects public OCEAN and Braiins inputs.

`Price` computes a shadow order and expected economics.

`Watch` records a bounded window without spending BTC.

`Mature` prevents the operator from judging evidence too early.

`Adapt` changes at most one strategy knob.

The allowed knobs are:

1. Depth target.
2. Overpay cushion.
3. Canary spend.
4. Duration.
5. Timing window.

Never change multiple knobs in one ratchet step.

## Manual Exposure Procedure

Manual exposure means the user placed a real Braiins order outside the app.

Immediately record it:

```bash
./scripts/ratchet position open --description "Braiins canary, 0.00010 BTC, 180 min, price 0.47741 BTC/EH/day, target OCEAN" --maturity-hours 72
```

Check positions:

```bash
./scripts/ratchet position list
```

Close only when the real position is finished:

```bash
./scripts/ratchet position close POSITION_ID
```

While any position is active:

1. The lifecycle enters manual exposure hold.
2. New watch experiments are blocked.
3. The engine should not open a new passive research stage.
4. The operator must supervise the real-world Braiins/OCEAN position.

## Background Engine

Start:

```bash
./scripts/ratchet engine start
```

Status:

```bash
./scripts/ratchet engine status
```

Stop:

```bash
./scripts/ratchet engine stop
```

Engine files:

1. PID: `data/supervisor.pid`.
2. Log: `logs/supervisor.log`.
3. State: `data/ratchet.sqlite`.

Crash behavior:

1. If the app crashes, the engine may keep running.
2. If the engine crashes, SQLite state remains.
3. If the Mac reboots, the engine is not guaranteed to restart automatically.
4. After reboot, run `./scripts/ratchet app` and start the engine again if desired.

## Switching To Another macOS Host

This is the safe migration procedure.

### On The Old Mac

Stop the background engine:

```bash
./scripts/ratchet engine stop
```

Check that it stopped:

```bash
./scripts/ratchet engine status
```

Commit and push source changes if any source files changed:

```bash
git status
git add README.md START_HERE.md docs src scripts tests macos config.example.toml pyproject.toml
git commit -m "Save Braiins Ratchet source state"
git push
```

Do not force commit runtime reports if you intentionally want them local only. If reports are part of the evidence you want on the new host, copy them in the backup step.

Create a state backup outside the repo or on external storage:

```bash
mkdir -p ~/Desktop/braiins-ratchet-backup
cp data/ratchet.sqlite* ~/Desktop/braiins-ratchet-backup/
cp -R reports ~/Desktop/braiins-ratchet-backup/
cp config.example.toml ~/Desktop/braiins-ratchet-backup/
```

Optional log backup:

```bash
cp -R logs ~/Desktop/braiins-ratchet-backup/
```

Do not copy `.venv` and do not copy `macos/build`. They are generated.

### On The New Mac

Clone the repository:

```bash
git clone -b master https://github.com/saymrwulf/BraiinsRatchet.git
cd BraiinsRatchet
```

Initialize runtime:

```bash
./scripts/ratchet setup
```

Restore state backup:

```bash
cp ~/Desktop/braiins-ratchet-backup/ratchet.sqlite* data/
cp -R ~/Desktop/braiins-ratchet-backup/reports .
cp ~/Desktop/braiins-ratchet-backup/config.example.toml config.example.toml
```

If you backed up logs:

```bash
cp -R ~/Desktop/braiins-ratchet-backup/logs .
```

Verify restored state:

```bash
./scripts/ratchet
./scripts/ratchet experiments
./scripts/ratchet position list
./scripts/ratchet engine status
```

Build and open the app:

```bash
./scripts/ratchet app
```

Start the engine only after verifying the state:

```bash
./scripts/ratchet engine start
```

### Migration With Active Manual Exposure

If a real Braiins order is active during migration:

1. Stop the engine on the old Mac.
2. Back up `data/ratchet.sqlite` and `reports/`.
3. Restore on the new Mac.
4. Run `./scripts/ratchet position list`.
5. Confirm the active exposure is still listed.
6. Do not start new experiments.
7. Start the engine only if you want it to hold and monitor around the active position.
8. Close the position only after the real Braiins/OCEAN exposure is finished.

The app cannot reconstruct unrecorded manual exposure. If the user placed an order but did not record it before migration, record it manually on the new host before starting experiments.

## State Recovery

### App Window Looks Wrong Or Old

Run:

```bash
./scripts/ratchet app
```

The launcher rebuilds the bundle, closes stale `BraiinsRatchetMac`, and opens the fresh app.

### Engine Status Looks Stale

Run:

```bash
./scripts/ratchet engine status
```

The status command checks the PID file and process table. If the PID file is stale, it clears itself when possible.

### A Watch Was Interrupted

Run:

```bash
./scripts/ratchet
./scripts/ratchet experiments
```

If a partial report exists, treat it as instrumentation evidence. Do not treat it as a full strategy result.

If the app says no watch process exists but the ledger shows an unfinished run marker, do not delete data immediately. First inspect:

```bash
./scripts/ratchet report
./scripts/ratchet experiments
```

Then either run a fresh `once` or start a new watch only if the cockpit says it is safe.

### SQLite State Exists But App Shows Empty

Check file location:

```bash
ls -l data/ratchet.sqlite
```

Run setup and next:

```bash
./scripts/ratchet setup
./scripts/ratchet
```

If the file was copied from another host while a process was writing to it, stop all engines and copy the database again from a clean backup.

### Reports Exist But Ledger Is Missing

If `reports/run-*.md` exists but `reports/EXPERIMENT_LOG.md` is missing, preserve the reports and restart normal monitoring. Future runs will recreate the ledger.

For old stored snapshots, use a retro report:

```bash
./scripts/ratchet retro 2026-04-25T19:08:00+00:00 2026-04-25T21:05:00+00:00
```

### Public Endpoint Failure

Symptoms:

1. `once` fails.
2. App remains stale.
3. Reports do not update.

Immediate response:

1. Do not bid.
2. Wait and retry later.
3. Use `Evidence` or `./scripts/ratchet report` to inspect last known state.

Fallback for manual market fixture:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli import-market examples/market_snapshot.example.json
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli evaluate
```

Manual imported snapshots are for debugging and should not be treated as live price action unless the operator created them from a current source.

## Backup Policy

Minimum backup:

1. `data/ratchet.sqlite*`.
2. `reports/`.
3. `config.example.toml` or any custom config file.

Optional backup:

1. `logs/`.
2. `results.tsv` if you use it for external analysis.

Do not back up as authoritative state:

1. `.venv`.
2. `macos/build`.
3. Python cache directories.
4. Swift build directories.

## Git Policy

The branch is `master`.

Before risky changes:

```bash
git status
```

After source changes:

```bash
./scripts/ratchet test
swift build --package-path macos/BraiinsRatchet
git add README.md START_HERE.md docs src scripts tests macos config.example.toml pyproject.toml
git commit -m "Describe the change"
git push
```

Do not commit owner tokens.

Be deliberate with `reports/`. Reports can be evidence, but local live reports may also be operational artifacts. Check `git status` before staging.

## Security Model

Allowed:

1. Public Braiins market data.
2. Public OCEAN dashboard data.
3. Watcher-only token only if future read-only account data is needed.

Forbidden:

1. Braiins owner token.
2. Any token that can place orders.
3. Any automatic spend path.
4. Any code path that modifies Braiins orders without a separate reviewed change.

If a secret is accidentally placed in the repo:

1. Stop work.
2. Remove it from files.
3. Rotate the secret at the provider.
4. Treat Git history as contaminated until cleaned.

## Diagnostics

Check app state:

```bash
./scripts/ratchet app-state
```

Check what the visible app surface believes it is showing:

```bash
./scripts/ratchet mirror
```

Check latest plain report:

```bash
./scripts/ratchet report
```

Check ledger:

```bash
./scripts/ratchet experiments
```

Check engine:

```bash
./scripts/ratchet engine status
```

Check lifecycle:

```bash
./scripts/ratchet supervise --status
```

Check manual exposure:

```bash
./scripts/ratchet position list
```

Check tests:

```bash
./scripts/ratchet test
```

Check Swift build:

```bash
swift build --package-path macos/BraiinsRatchet
```

## Release Checklist

Before pushing a release-quality change:

1. Run `./scripts/ratchet test`.
2. Run `swift build --package-path macos/BraiinsRatchet`.
3. Run `./scripts/build_mac_app`.
4. Run `./scripts/ratchet app`.
5. Confirm the app opens as the native Flight Deck.
6. Confirm `git status` does not accidentally include runtime-only reports.
7. Commit on `master`.
8. Push to GitHub.

## Operator Do-Not-Do List

Do not delete `data/ratchet.sqlite` unless intentionally resetting all local lifecycle state.

Do not copy a live SQLite file while the engine is writing unless you have stopped the engine first.

Do not start two watches at the same time.

Do not run terminal watches while the app says the engine owns control.

Do not treat cooldown as wasted time.

Do not change more than one strategy knob per ratchet step.

Do not let an unrecorded manual Braiins order exist outside the ledger.

Do not use a Braiins owner token in this project.
