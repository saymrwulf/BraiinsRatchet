# Program Charter

## Goal

Maximize expected BTC profit, or minimize BTC loss, for manually buying BTC hashpower on Braiins and pointing it at OCEAN/DATUM.

## Operating Premises

- OCEAN uses TIDES: shares are paid only if they are inside the current share-log when OCEAN finds a block.
- OCEAN block discovery is stochastic and memoryless. A recent drought is not evidence that OCEAN is "due".
- The useful edge is expected value versus Braiins market price, plus operational quality and timing around observable fee/reward conditions.
- The system should improve through repeated small experiments, not through one large theoretical bet.

## Ratchet Loop

1. Collect read-only snapshots from OCEAN, Braiins, local DATUM/Knots where available, and manual experiment results.
2. Score candidate policies against current guardrails and historical/paper-trade results.
3. Emit a manual recommendation.
4. If the recommendation is executed manually, record the exact order parameters and later realized rewards.
5. Keep changes to `strategy.py` only when they improve the measured score under comparable risk.

## Hard Guardrails

- No code path places, modifies, or cancels Braiins orders.
- No owner token may be stored, loaded, or requested by the code.
- Watcher-only Braiins token may be provided via environment variable only.
- No secrets in Git.
- No containers or VMs.
- Runtime files stay inside this repository.
- Default branch name is `master`.
- Production-like behavior starts with monitor-only and paper trading.
- First live canary, if manually executed, should use minimum viable spend only.

## Initial Scoring Metric

Use BTC-denominated expected value:

```text
expected_net_btc = expected_ocean_rewards_after_fee - braiins_cost_btc
score = expected_net_btc - risk_penalty_btc - execution_penalty_btc
```

The strategy must show break-even price, discount to break-even, spend, duration, and maturity assumptions.

