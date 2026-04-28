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
- Mission Control with one explicit next action.
- Research Map with the full ratchet pathway.
- Direct watch-only controls without an approval gate.
- Manual exposure recording and closing controls.
- Advanced panel for raw artifacts and backend diagnostics.
- Ratchet Lecture for the general autoresearch method.
- Monitor-only. It never places Braiins orders.

## Product Direction

The next production step is wiring LaunchAgent controls for the durable supervisor while keeping Mission Control domain-first.
