# Braiins Ratchet Mac

Native SwiftUI shell for the durable Braiins Ratchet lifecycle engine.

The Python supervisor remains the source of truth. This app reads the same repository-local SQLite state through `./scripts/ratchet`.

## Normal Run

```bash
./scripts/ratchet app
```

This builds `macos/build/Braiins Ratchet.app` and opens the packaged app. Use this path for normal operation.

## Current Scope

- Native macOS SwiftUI cockpit.
- Liquid-glass-inspired material panels.
- Buttons for cockpit, lifecycle status, automation proposal, and full report.
- Manual exposure recording and closing controls.
- Monitor-only. It never places Braiins orders.

## Product Direction

The next production step is wiring LaunchAgent controls for the durable supervisor.
