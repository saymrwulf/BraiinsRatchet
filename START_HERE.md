# Start Here

This project now has one operator entry point:

```bash
./scripts/ratchet
```

That is the same as:

```bash
./scripts/ratchet next
```

It prints the cockpit: current state, exact next action, interpretation, reference commands, and ratchet rule.

## Your Job

Your job is not to understand every metric.

Your job is:

1. Run `./scripts/ratchet`.
2. Do only what it says under `DO THIS NOW`.
3. Ignore every other command unless `DO THIS NOW` tells you to run it.
4. If it tells you to run `./scripts/ratchet watch 2`, start it, leave the terminal open, and come back after about 2 hours.
5. If you manually place a Braiins canary, write down the order details outside this repo and wait through the maturity window before judging it.

## Who Is In Control?

If `watch` is running, the Python process is in control of that terminal.

You do not need to babysit it. It will:

1. Collect samples every 5 minutes.
2. Write the run report when it finishes.
3. Print the cockpit again.
4. Return control to your shell prompt.

If you want the technical report, run `./scripts/ratchet report`. The normal workflow intentionally shows the cockpit first.

After a watch finishes, the cockpit enters a post-watch cooldown. That is deliberate.

Post-watch cooldown means:

1. The current experimental stage is complete.
2. Starting another identical watch immediately is not useful ratcheting.
3. The run report is the evidence artifact.
4. The next planned touch is a later fresh sample, usually `./scripts/ratchet once`.

## Research Pathway

The cockpit has two different time horizons:

1. `DO THIS NOW` is the only command you should run next.
2. `Ratchet Pathway Forecast` tells you what the next stages probably look like.

The forecast is not a profit prediction. It is a workload and research-flow prediction.

It is split into:

1. `Immediate`: what happens now.
2. `Midterm`: what probably happens after the current run or sample.
3. `Longterm`: what could happen after multiple reports mature.

Expect the pathway to change after each report. That is the point of ratcheting: the next stage adapts to measured evidence instead of following a rigid plan.

## What The Actions Mean

`observe` means do not bid.

`manual_canary` means a tiny research experiment is inside the configured loss budget. It is not a profit signal.

`manual_bid` means the stricter profit-seeking guardrails cleared. The code still does not place the order. You decide manually in Braiins.

## Where The Reports Are

The master ledger is:

```text
reports/EXPERIMENT_LOG.md
```

Each completed watch creates one run report:

```text
reports/run-*.md
```

Older sessions can be embedded with:

```bash
./scripts/ratchet retro START_UTC END_UTC
```

## The Ratchet Rule

One run is not a verdict. One run is a measurement.

Only change one knob at a time:

1. Depth target.
2. Overpay cushion.
3. Canary spend.
4. Duration.
5. Timing window.

Do not increase spend until multiple mature runs point in the same direction.
