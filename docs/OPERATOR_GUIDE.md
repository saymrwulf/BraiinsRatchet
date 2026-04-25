# Operator Guide

This project is a monitor and decision aid. It does not place Braiins orders.

Think of it in Karpathy autoresearch terms:

1. Observe the world.
2. Score one small candidate action.
3. Do nothing unless the score clears strict guardrails.
4. If you manually act, wait for the result to mature.
5. Ratchet the strategy only after measured evidence improves.

## First-Time Setup

From the repository root:

```bash
./scripts/ratchet setup
```

What this does:

- Creates `.venv` inside this repo if needed.
- Initializes `data/ratchet.sqlite`.
- Does not install packages.
- Does not touch anything outside the repo.

## First Live Check

Run:

```bash
./scripts/ratchet once
```

What this does:

- Fetches one OCEAN snapshot.
- Fetches one public Braiins market snapshot without a token.
- Computes the current breakeven and strategy recommendation.
- Prints a report.

It intentionally hides raw JSON. If debugging is needed, use:

```bash
./scripts/ratchet raw-cycle
```

## How To Read The Report

Focus on `Strategy action`.

If it says:

```text
Strategy action: observe
```

Do not place a bid. The market is not cheap enough or required data is missing.

If it says:

```text
Strategy action: manual_bid
```

The strategy thinks a small manual profit-seeking bid clears the configured discount guardrails. You still decide manually in the Braiins UI.

If it says:

```text
Strategy action: manual_canary
```

The market is not a money-printer setup, but the expected loss is inside the configured research budget. This is the scientific mode: a tiny canary may be useful to learn about execution, timing, OCEAN accounting, stale/reject behavior, and TIDES maturity.

Important fields:

- `best_ask_btc_per_eh_day`: current buy reference from Braiins.
- `breakeven_btc_per_eh_day`: estimated mining EV at current OCEAN/network inputs.
- `score_btc`: risk-adjusted expected value. Negative means no action.
- `proposed_spend_btc`: canary spend, currently tiny by design.
- `maturity`: how long to wait before judging a manually executed canary.

## Normal Monitoring Session

Run:

```bash
./scripts/ratchet watch 6
```

This watches for about 6 hours, sampling every 5 minutes.

During the watch:

- Leave the terminal open.
- Do not babysit every line.
- If it prints `observe`, do nothing.
- If it prints `manual_bid`, stop and run `./scripts/ratchet report` before deciding manually.

Stop early with `Ctrl-C`.

## When To Act

Only consider a profit-seeking manual bid when all of these are true:

- `Strategy action: manual_bid`.
- `score_btc` is positive.
- `best_ask_btc_per_eh_day` is below the guardrail-adjusted breakeven.
- The proposed spend is acceptable to lose.
- You can wait through the maturity window before judging the result.

Do not act because OCEAN is "due". Block discovery is memoryless.

Only consider a research canary when all of these are true:

- `Strategy action: manual_canary`.
- `proposed_spend_btc` is acceptable to lose.
- `expected_net_btc` is not worse than the configured canary loss budget.
- You are explicitly buying information, not pretending the edge is proven.
- You can wait through the maturity window before judging the result.

## How Long To Wait After A Manual Canary

Use the report's `maturity` line.

With the current OCEAN estimate, it is about:

```text
72 hours
```

That comes from the 8-block TIDES window and about 9 hours expected OCEAN block time. Do not judge the experiment after only minutes or a few hours.

## Daily Routine

Practical routine:

1. Morning: `./scripts/ratchet once`
2. If `observe`: do nothing.
3. If you want live monitoring: `./scripts/ratchet watch 6`
4. If `manual_bid`: inspect `./scripts/ratchet report`
5. If you manually place a canary, write down the Braiins order parameters and wait through the maturity window.

## Safety Boundaries

- No owner token goes into this repo.
- No watcher token is needed for public price monitoring.
- No code here places orders.
- `.venv` and `data/` are local runtime state.
- The Git branch is `master`.
