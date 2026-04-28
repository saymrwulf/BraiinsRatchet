# Braiins Ratchet Mac

Native SwiftUI control room for the durable Braiins Ratchet lifecycle engine.

The Python lifecycle engine remains the source of truth. This app reads the same repository-local SQLite state through structured app state, not by making the Flight Deck a terminal transcript.

## Normal Run

```bash
./scripts/ratchet app
```

This builds `macos/build/Braiins Ratchet.app`, closes any stale `BraiinsRatchetMac` UI process, and opens the fresh packaged app. Use this path for normal operation.

## Current Scope

- Native macOS Tahoe SwiftUI Flight Deck.
- Real Liquid Glass APIs: `glassEffect`, `GlassEffectContainer`, `.glass`, `.glassProminent`, toolbar search, and `backgroundExtensionEffect`.
- Hashflow view for Umbrel, Knots, Datum, OCEAN, and Braiins interplay.
- Ratchet view for the full autoresearch pathway.
- Bid Lab for shadow orders and loss boundaries.
- Forever Engine controls for the monitor-only background lifecycle.
- Manual exposure recording and closing controls.
- Evidence view for raw artifacts and backend diagnostics.
- Monitor-only. It never places Braiins orders.

## Product Direction

The next production step is optional LaunchAgent integration. The current app already starts and stops a repo-local background monitor engine.
