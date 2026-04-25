# Braiins Public Market Collector

The public Braiins Hashpower page loads market data from unauthenticated browser endpoints under:

```text
https://hashpower.braiins.com/webapi
```

The monitor-only collector currently reads:

- `/spot/stats`: market status, last average price, total available hashrate, matched hashrate.
- `/orderbook`: public bids and asks.

No token is required for these calls. The collector does not send an `apikey` header and only performs HTTP `GET`.

## Price Selection

For a buyer, the conservative live reference price is:

1. Best ask, if available.
2. Last average price, if no ask exists.
3. Best bid, if neither ask nor last price exists.

The chosen value is stored as `best_price_btc_per_eh_day` for strategy evaluation. The raw fields are also stored:

- `best_bid_btc_per_eh_day`
- `best_ask_btc_per_eh_day`
- `last_price_btc_per_eh_day`
- `total_hashrate_eh_s`
- `available_hashrate_eh_s`
- `status`

## Commands

Collect one public Braiins snapshot:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli collect-braiins-public
```

Then evaluate the current strategy:

```bash
PYTHONPATH=src ./.venv/bin/python -m braiins_ratchet.cli evaluate
```

## Failure Mode

These endpoints are discovered from the public web app, not from a stable public API contract. If Braiins changes field names or requires authentication later, tests and collection should fail visibly. Do not add an owner token to recover functionality.

