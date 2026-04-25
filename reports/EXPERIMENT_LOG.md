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
