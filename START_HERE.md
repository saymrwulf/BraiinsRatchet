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
