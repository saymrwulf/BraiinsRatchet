# Braiins Ratchet Mac

Native SwiftUI shell for the durable Braiins Ratchet lifecycle engine.

The Python supervisor remains the source of truth. This app reads the same repository-local SQLite state through `./scripts/ratchet`.

## Run From Source

```bash
cd macos/BraiinsRatchet
swift run BraiinsRatchetMac
```

## Current Scope

- Native macOS SwiftUI cockpit.
- Liquid-glass-inspired material panels.
- Buttons for cockpit, lifecycle status, automation proposal, and full report.
- Monitor-only. It never places Braiins orders.

## Product Direction

The next production step is packaging this SwiftUI shell as a signed `.app` and wiring LaunchAgent controls for the durable supervisor.
