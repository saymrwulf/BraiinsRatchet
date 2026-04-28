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
2. Stay on `Mission Control` unless you intentionally need raw diagnostics.
3. Read `Current Decision` first.
4. Read `Who Is In Control` second.
5. Use `Next Passive Action` only when it is enabled.
6. If you manually place a Braiins canary, record it in `Manual Exposure` immediately.

Do not start extra terminal watches while the app says a watch, cooldown, or manual exposure owns control.

## Who Is In Control?

The app has one ownership model:

1. `The app is ready`: you may start the enabled passive action.
2. `A watch run owns control`: leave it alone until it finishes.
3. `Cooldown owns control`: wait until the shown earliest action time.
4. `Manual exposure owns control`: supervise the real-world Braiins/OCEAN position and do not start new experiments.
5. `The app is busy`: a monitor-only backend operation is running right now.

This is the anti-babysitting rule: if the app says something else owns control, your workload is zero unless you are supervising a real manual exposure.

## What The App Does

The app is monitor-only. It never places, modifies, or cancels Braiins orders.

It can:

1. Read persisted lifecycle state from `data/ratchet.sqlite`.
2. Collect OCEAN and public Braiins market samples.
3. Run passive watch-only research windows.
4. Write run reports under `reports/`.
5. Track manually executed Braiins exposure that you enter yourself.
6. Resume from the same SQLite state after a crash or reboot.

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

The app is organized as:

1. `Mission Control`: current decision, control ownership, next passive action, progress, evidence, and plain English interpretation.
2. `Research Map`: visual autoresearch stage model.
3. `Manual Exposure`: record or close manually executed Braiins exposure.
4. `Advanced`: raw cockpit, report, and ledger artifacts for diagnostics.
5. `Ratchet Lecture`: the general observe, hypothesize, bound, mature, adapt method.

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

Use the app's `Advanced` tab when you need raw artifacts. Mission Control intentionally hides raw logs during normal operation.

## Advanced Fallback Commands

Use these only if the native app cannot be opened or you are debugging:

```bash
./scripts/ratchet
./scripts/ratchet once
./scripts/ratchet watch 2
./scripts/ratchet supervise
./scripts/ratchet position list
./scripts/ratchet report
./scripts/ratchet experiments
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
