# Braiins Ratchet Mac

Native SwiftUI control room for the durable Braiins Ratchet lifecycle engine.

The Python lifecycle engine remains the source of truth. This app reads the same repository-local SQLite state through structured app state, not by making Mission Control a terminal transcript.

## Normal Run

```bash
./scripts/ratchet app
```

This builds `macos/build/Braiins Ratchet.app` and opens the packaged app. Use this path for normal operation.

## Current Scope

- Native macOS SwiftUI control room.
- Mission Control with one explicit decision and control owner.
- Mining Stack view for Umbrel, Knots, Datum, OCEAN, and Braiins interplay.
- Ratchet view for the full autoresearch pathway.
- Strategy Lab for shadow orders and loss boundaries.
- Forever Engine controls for the monitor-only background lifecycle.
- Manual exposure recording and closing controls.
- Evidence Vault for raw artifacts and backend diagnostics.
- Monitor-only. It never places Braiins orders.

## Product Direction

The next production step is optional LaunchAgent integration. The current app already starts and stops a repo-local background monitor engine.
