# Braiins Ratchet User Guide

This guide is for operating the app without needing to understand the code.

The short version is:

1. Open the app with `./scripts/ratchet app`.
2. Stay on `Flight Deck`.
3. Read the giant decision word.
4. If the app says `ENGINE LIVE`, leave it alone.
5. If you manually place a Braiins order, immediately record it in `Exposure`.
6. Never start a second watch when the app says a watch, cooldown, engine, or exposure owns control.

## The Story

Braiins Ratchet is a research cockpit for one question:

Can we find better timing and sizing rules for manually buying hashpower on Braiins and pointing it at OCEAN, while minimizing loss and learning fast?

The system does not try to be a money printer. It does not assume that every opportunity must be profitable. It treats each run as an experiment. A small expected loss can be acceptable if it buys useful information and stays inside the configured research budget.

The app is monitor-only. It never places, modifies, or cancels Braiins orders. You remain the only actor with owner-token power.

## What The Tool Controls

The tool can influence only the research process:

1. When to observe.
2. When to run a passive watch.
3. How to evaluate public Braiins prices against OCEAN mining economics.
4. How to record evidence.
5. When to stop repeating the same experiment.
6. When manual exposure blocks further experiments.
7. Which strategy knob may be changed next.

The tool does not control:

1. Bitcoin price.
2. Global hashrate.
3. Energy prices.
4. OCEAN block luck.
5. Braiins order matching.
6. Your Umbrel, Knots, Datum, or OCEAN account.
7. Any Braiins owner-token action.

## Your Mental Model

Think of the system as a laboratory wheel:

1. `Sense`: fetch OCEAN and Braiins public market data.
2. `Price`: compute current breakeven and shadow order economics.
3. `Watch`: collect a bounded time window without spending BTC.
4. `Mature`: wait long enough that the last evidence is not misread.
5. `Adapt`: change exactly one knob only if the evidence justifies it.

This is the Karpathy-style ratchet. One run does not prove a strategy. One run moves the wheel by one click.

## First Open

From the repository root:

```bash
./scripts/ratchet app
```

This rebuilds and opens the native macOS app. If an old Braiins Ratchet window is open, the launcher replaces it with the fresh app.

The normal app tabs are:

1. `Flight Deck`: main decision cockpit.
2. `Hashflow`: how Umbrel, Knots, Datum, Braiins, OCEAN, and block luck interact.
3. `Ratchet`: the autoresearch loop and time horizons.
4. `Bid Lab`: shadow order, breakeven, expected net, and loss budget.
5. `Exposure`: manual Braiins position recorder.
6. `Evidence`: raw reports and diagnostic text.
7. `Reality Mirror`: the app's self-reflective BED view.

If you are unsure, stay on `Flight Deck`.

## Reality Mirror

The `Reality Mirror` is the app looking at itself.

BED means `Backstage Evidence Deck`.

It exists because generic advice is not enough. The app writes what it believes it is rendering right now:

1. Visible section.
2. Giant decision word.
3. Control owner.
4. Next action.
5. Engine state.
6. Strategy action.
7. Braiins freshness.
8. Active watch, cooldown, or manual exposure.
9. Buttons it believes are visible.
10. Operator truths for the current state.

The files are:

```text
data/app_visual_state.md
data/app_visual_state.json
```

If you ask for help, run:

```bash
./scripts/ratchet mirror
```

That prints the latest self-written visual state, so the helper can reason about what is actually on your app surface.

## Flight Deck Reading Order

Read the screen in this order every time:

1. The giant decision word.
2. The `control` puck.
3. The `next` puck.
4. The four instrument chips.
5. The `Forever Engine` panel.

Do not start by reading raw reports. Raw reports are for checking details after the app tells you why they matter.

## The Decision Words

`LOAD` means the app is reading local state.

What you do: wait a few seconds.

`REFRESH` means the latest market data is missing or stale.

What you do: press `One Sample` or use the toolbar refresh path if enabled.

`WATCH` means a passive watch is useful.

What you do: prefer `Start Forever Engine` if you want the app to keep running the lifecycle. If you are using terminal fallback, run one watch only.

`ENGINE LIVE` means the forever engine owns passive research.

What you do: do nothing. Leave the app open or closed. The background engine keeps the monitor-only lifecycle moving.

`WAIT` means a watch is already running.

What you do: do not start anything else. The Flight Deck should show a running-experiment progress panel with progress percent, approximate cycle count, and local finish time.

`COOLDOWN` means the last watch already produced evidence and the system is intentionally waiting.

What you do: wait until the earliest action time shown by the app.

`HOLD` means a manual Braiins exposure is active.

What you do: supervise the real-world position and do not start new experiments.

`REVIEW` means the stricter profit-seeking guardrails produced a manual review signal.

What you do: read `Bid Lab` and `Evidence`. Any Braiins order still remains manual.

`OBSERVE` means no useful action window is visible.

What you do: do not bid. Waiting is a valid action.

## The Three Strategy States

`observe` means the model does not recommend a bid or canary now.

Correct interpretation: the tool sees no useful window. This is not failure. It is evidence that the current market state did not clear even the research trigger.

`manual_canary` means a tiny research canary is inside the configured expected-loss budget.

Correct interpretation: this is not a profit claim. It means the system may recommend learning from a small bounded experiment, or watching the window more carefully before any manual spend.

`manual_bid` means the stricter profit-seeking guardrails cleared.

Correct interpretation: this is still not automatic execution. It is a manual review signal. You must inspect the evidence before doing anything in Braiins.

## What A Passive Watch Does

A passive watch does not spend BTC.

It collects repeated samples:

1. OCEAN pool and network state.
2. Public Braiins market data.
3. A strategy proposal for each sample.
4. A run report under `reports/run-*.md`.
5. A ledger entry in `reports/EXPERIMENT_LOG.md`.

The default watch stage used by the forever engine is 2 hours. It samples every 5 minutes, so a full stage normally has 24 cycles.

During a watch, the app shows the active run id, countdown, progress bar, approximate cycle count, and local finish time. The visual countdown updates every second. Backend state refreshes about every 30 seconds.

## What The Forever Engine Does

`Start Forever Engine` starts a repo-local background monitor loop.

The loop is:

1. Resume local SQLite state.
2. If a manual exposure is active, hold.
3. If cooldown is active, wait.
4. If ready, run one 2-hour passive watch.
5. Write reports and ledger entries.
6. Enter cooldown.
7. Repeat until stopped.

It never places Braiins orders.

If the app or Mac restarts, open the app again and start the engine again if needed. The app reads the same SQLite state and continues from the last recorded phase.

## The Time Horizons

The app always has three horizons.

`Immediate` means what is useful now.

Examples: wait, refresh once, hold exposure, start engine, inspect report.

`Midterm` means what is likely after the current stage finishes.

Examples: after cooldown, collect one fresh sample; after a watch, compare the run report; after manual exposure, close the position when finished.

`Longterm` means what may become reasonable only after repeated evidence.

Examples: lower overpay cushion, change depth target, change canary duration, change canary spend, test a different timing window.

Workflow probabilities are not profit probabilities. They estimate what the research process will probably ask you to do, not whether mining will win.

## What Counts As Evidence

Evidence is not a feeling. Evidence is written state.

Useful evidence includes:

1. A completed run report in `reports/run-*.md`.
2. A ledger entry in `reports/EXPERIMENT_LOG.md`.
3. A sequence of stored Braiins market snapshots.
4. A sequence of stored OCEAN snapshots.
5. A manually recorded exposure with opening and closing information.

Not evidence:

1. A single scary red number during a running watch.
2. OCEAN feeling due for a block.
3. A best ask that disappears before executable depth exists.
4. An unrecorded manual Braiins order.
5. A result judged before the OCEAN share window has had time to mature.

## Potential Findings

The ratchet can find several useful things even if no profit appears.

Finding type 1: Braiins price is usually too close to breakeven.

Response: keep observing; do not escalate spend.

Finding type 2: canary windows appear, but only at very shallow depth.

Response: test a smaller depth target before changing spend.

Finding type 3: overpay cushion dominates the loss.

Response: lower the overpay cushion for the next experiment.

Finding type 4: windows are time-of-day dependent.

Response: test a timing window, but keep all other knobs unchanged.

Finding type 5: OCEAN variance overwhelms short runs.

Response: increase patience and maturity tracking, not spend.

Finding type 6: manual execution friction is the biggest cost.

Response: improve operator procedure before strategy complexity.

Finding type 7: profit-seeking guardrails occasionally clear.

Response: inspect the full report and decide manually. Record any exposure immediately.

## The One-Knob Rule

Only change one knob at a time:

1. Depth target.
2. Overpay cushion.
3. Canary spend.
4. Duration.
5. Timing window.

If two knobs change together, the next run cannot tell which knob mattered.

## Manual Braiins Action Procedure

Only you can place a Braiins order.

Before doing anything in Braiins:

1. Confirm the app says `REVIEW` or the evidence explicitly supports a small `manual_canary`.
2. Open `Bid Lab`.
3. Read price, spend, duration, expected net, breakeven, and reason.
4. Decide whether the proposed spend is acceptable to lose.
5. Place the order manually only if you still want to.
6. Immediately record the exposure in `Exposure`.

When recording exposure, include enough text that future you understands it:

```text
Braiins canary, 0.00010 BTC, 180 min, price 0.47741 BTC/EH/day, target OCEAN
```

After recording exposure, the app should enter `HOLD`.

Do not start new watch experiments while real exposure is active.

## Maturity Rule

Do not judge a manual canary immediately after it ends.

OCEAN payouts depend on share accounting and block luck. The app currently treats canary evidence as immature for roughly the OCEAN share-log window, often about 72 hours with the current assumptions.

During maturity:

1. Do not declare victory.
2. Do not declare failure.
3. Do not increase spend.
4. Keep the exposure recorded.
5. Close it only when the real Braiins/OCEAN position is finished and you are ready to resume research.

## Crash Or Reboot

If the app crashes:

1. Reopen it with `./scripts/ratchet app`.
2. Read `Flight Deck`.
3. If the engine is not running and you want continuous monitoring, press `Start Forever Engine`.

If the Mac reboots:

1. Open Terminal.
2. Go to the repo.
3. Run `./scripts/ratchet app`.
4. Read `Flight Deck`.
5. Start the engine if you want the lifecycle to continue.

The important state is in `data/ratchet.sqlite`, not in the app window.

## What Not To Do

Do not start multiple watches.

Do not treat `manual_canary` as a profit signal.

Do not place an order because OCEAN feels due.

Do not increase spend after one lucky result.

Do not change several strategy knobs together.

Do not use owner tokens in this repo.

Do not delete `data/ratchet.sqlite` unless you intentionally want to lose local state.

## Where To Look When Confused

Use this order:

1. `Flight Deck`: what to do now.
2. `Ratchet`: where the experiment is in the loop.
3. `Bid Lab`: why the current proposal exists.
4. `Exposure`: whether real money blocks new experiments.
5. `Reality Mirror`: what the app believes it is showing right now.
6. `Evidence`: raw report and ledger.
7. `docs/OPERATOR_GUIDE.md`: installation, recovery, migration, and diagnostics.

## Glossary

`Braiins`: the hashpower marketplace where you can manually buy temporary hashrate.

`OCEAN`: the mining pool where the purchased hashrate is pointed.

`Umbrel`: your local host environment.

`Knots`: your Bitcoin node implementation.

`Datum`: the mining template and routing path.

`TIDES`: OCEAN payout accounting model with a share window.

`Breakeven`: estimated Braiins price where expected mining reward equals spend.

`Expected net`: modeled reward minus spend before real-world luck.

`Score`: expected net after downside penalty.

`Canary`: tiny experiment that may lose money but should buy information.

`Manual exposure`: a real Braiins order you placed manually and recorded in the app.
