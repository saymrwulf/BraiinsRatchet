# Start Here

This project now has one operator entry point:

```bash
./scripts/ratchet
```

That is the same as:

```bash
./scripts/ratchet next
```

It prints the cockpit: current state, exact next action, interpretation, safe commands, and ratchet rule.

## Your Job

Your job is not to understand every metric.

Your job is:

1. Run `./scripts/ratchet`.
2. Do the first item under `What You Do Now`.
3. If a watch is running, leave it alone until it finishes.
4. After a watch finishes, run `./scripts/ratchet` again.
5. If you manually place a Braiins canary, write down the order details outside this repo and wait through the maturity window before judging it.

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
