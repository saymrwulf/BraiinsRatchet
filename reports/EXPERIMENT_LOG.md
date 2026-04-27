# Experiment Log

Karpathy-style ratchet rule: every run states a hypothesis, collects data, scores the current strategy, and records the next adaptation.

## retro-2026-04-25T16-35-00-00-00

- status: retroactive
- started_utc: 2026-04-25T16:35:00+00:00
- ended_utc: 2026-04-25T18:32:00+00:00
- hypothesis: Retroactively embed an already completed manual watch into the ratchet ledger.
- plan: reconstruct from stored snapshots because this run happened before automatic run bookkeeping existed.
- collected_samples: 27
- action_counts: manual_canary=27
- report: reports/retro-2026-04-25T16-35-00-00-00.md
- adaptation: The run repeatedly found bounded canary conditions and average modeled net was slightly positive. Next ratchet: keep spend tiny, test whether the same window survives a lower overpay cushion.

## retro-2026-04-25T19-08-00-00-00

- status: retroactive
- started_utc: 2026-04-25T19:08:00+00:00
- ended_utc: 2026-04-25T21:05:00+00:00
- hypothesis: Retroactively embed an already completed manual watch into the ratchet ledger.
- plan: reconstruct from stored snapshots because this run happened before automatic run bookkeeping existed.
- collected_samples: 24
- action_counts: manual_canary=24
- report: reports/retro-2026-04-25T19-08-00-00-00.md
- adaptation: The run repeatedly found bounded canary conditions, but modeled net was negative on average. Next ratchet: do not escalate spend; test a smaller depth target or a lower overpay cushion.

## run-20260427T135327Z-222826

- status: running
- started_utc: 2026-04-27T13:53:27+00:00
- planned_cycles: 24
- interval_seconds: 300
- planned_duration_minutes: 120.0
- hypothesis: Depth-aware fillable price plus a small overpay cushion is a better canary trigger than raw best ask.
- plan: collect public Braiins depth, collect OCEAN state, compute shadow canary, store every proposal.
- operator_action: none by default; manual action only if report later says manual_canary or manual_bid and operator agrees.

- status_update: completed
- ended_utc: 2026-04-27T15:48:52+00:00
- collected_samples: 24
- action_counts: manual_canary=24
- strategy_price_min_avg_max: 0.47763 / 0.4798921698412225 / 0.48492
- expected_net_min_avg_max_btc: -0.00000383101148933686517479144602 / -0.000002821503981988926325106899014 / -0.00000236319764547711127977695701
- latest_action: manual_canary
- latest_reason: bounded research canary: profit guardrails not cleared, but expected_net=-0.00000238363529903760002629072482 is within loss budget 0.000025
- report: reports/run-20260427T135327Z-222826.md
- adaptation: The run repeatedly found bounded canary conditions, but modeled net was negative on average. Next ratchet: do not escalate spend; test a smaller depth target or a lower overpay cushion.
