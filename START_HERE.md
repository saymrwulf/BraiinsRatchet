# Start Here

This project now has one normal operator entry point:

```bash
./scripts/ratchet app
```

That command builds and opens the native macOS app. The app is the control room. The terminal is only the launcher and fallback diagnostic path.

## Your Job

Your job is not to understand every metric.

Your job is:

1. Open the app with `./scripts/ratchet app`.
2. Stay on `Flight Deck` unless you intentionally need another tab.
3. Read the giant decision word first.
4. Read the glass `control` and `next` pucks second.
5. Prefer `Start Forever Engine` when you want the app to keep the monitor-only lifecycle moving without babysitting.
6. If you manually place a Braiins canary, record it in `Exposure` immediately.

Do not start extra terminal watches while the app says a watch, cooldown, or manual exposure owns control.

## Who Owns Control?

The app has one ownership model:

1. `The app is ready`: you may start the enabled passive action.
2. `Forever engine`: the background monitor engine owns passive sampling; leave it alone.
3. `A watch run owns control`: leave it alone until it finishes.
4. `Cooldown owns control`: wait until the shown earliest action time.
5. `Manual exposure owns control`: supervise the real-world Braiins/OCEAN position and do not start new experiments.
6. `The app is busy`: a monitor-only backend operation is running right now.

This is the anti-babysitting rule: if the app says something else owns control, your workload is zero unless you are supervising a real manual exposure.

## What The App Does

The app is monitor-only. It never places, modifies, or cancels Braiins orders.

It can:

1. Read persisted lifecycle state from `data/ratchet.sqlite`.
2. Collect OCEAN and public Braiins market samples.
3. Run passive watch-only research windows.
4. Write run reports under `reports/`.
5. Track manually executed Braiins exposure that you enter yourself.
6. Start or stop a repo-local forever monitor engine.
7. Resume from the same SQLite state after a crash or reboot.

## Native Mac App

The native SwiftUI app is in:

```text
macos/BraiinsRatchet
```

Build and open the real app bundle:

```bash
./scripts/ratchet app
```

This creates `macos/build/Braiins Ratchet.app`. After that, you can open that app bundle directly from Finder or pin it in the Dock.

The launcher rebuilds the app and replaces any already-running `BraiinsRatchetMac` UI process before opening the bundle. That prevents macOS from simply focusing an old window after a redesign.

The app is organized as:

1. `Flight Deck`: giant decision word, glass control pucks, reactor lens, engine controls, and key instruments.
2. `Hashflow`: the Umbrel, Knots, Datum, OCEAN, and Braiins interplay.
3. `Ratchet`: the observe, price, watch, mature, adapt learning loop.
4. `Bid Lab`: shadow order, expected net, breakeven, and loss boundary.
5. `Exposure`: record or close manually executed Braiins exposure.
6. `Evidence`: raw cockpit, report, and ledger artifacts for diagnostics.
7. `Reality Mirror`: self-reflective BED view that shows what the app believes it is rendering right now.

The small `Reality Mirror` HUD writes the current visual/operator truth to:

```text
data/app_visual_state.md
data/app_visual_state.json
```

If you ask for help, this file is the fastest way to show the exact app state instead of describing it from memory:

```bash
./scripts/ratchet mirror
```

## Research Pathway

The app has three time horizons:

1. `Immediate`: what can happen now, usually start, wait, refresh, or hold.
2. `Midterm`: what probably happens after the current watch, cooldown, or manual exposure matures.
3. `Longterm`: what could happen after multiple evidence artifacts point in the same direction.

The pathway is allowed to change after each report. That is the point of ratcheting: the next stage adapts to measured evidence instead of following a rigid plan.

## What The Actions Mean

`observe` means do not bid.

`manual_canary` means a tiny research experiment is inside the configured loss budget. It is not a profit signal.

`manual_bid` means the stricter profit-seeking guardrails cleared. The code still does not place the order. You decide manually in Braiins.

## Where The Evidence Lives

The master ledger is:

```text
reports/EXPERIMENT_LOG.md
```

Each completed watch creates one run report:

```text
reports/run-*.md
```

Use the app's `Evidence` tab when you need raw artifacts. Flight Deck intentionally hides raw logs during normal operation.

## Full Guides

Read the user guide when you want the complete noob-friendly story:

```bash
./scripts/ratchet guide
```

Read the operator guide when you need installation, migration to another Mac, backup, recovery, or architecture:

```bash
./scripts/ratchet operator-guide
```

## Advanced Fallback Commands

Use these only if the native app cannot be opened or you are debugging:

```bash
./scripts/ratchet
./scripts/ratchet once
./scripts/ratchet watch 2
./scripts/ratchet supervise
./scripts/ratchet engine status
./scripts/ratchet engine start
./scripts/ratchet engine stop
./scripts/ratchet position list
./scripts/ratchet report
./scripts/ratchet experiments
./scripts/ratchet mirror
./scripts/ratchet guide
./scripts/ratchet operator-guide
```

The preferred workflow remains the native app.

## The Ratchet Rule

One run is not a verdict. One run is a measurement.

Only change one knob at a time:

1. Depth target.
2. Overpay cushion.
3. Canary spend.
4. Duration.
5. Timing window.

Do not increase spend until multiple mature runs point in the same direction.
