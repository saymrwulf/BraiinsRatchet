# Reboot Handoff

Generated: 2026-05-04 Europe/Zurich

## Current Truth Before Reboot

- Repository: `/Users/oho/GitClone/CodexProjects/BraiinsRatchet`
- Branch: `master`
- Latest pushed code commit: `b17c6aa Treat failed watches as instrumentation backoff`
- Forever engine: intentionally stopped before reboot
- Active watch: none detected
- Active manual Braiins exposure: none recorded
- Latest stored OCEAN sample: `2026-04-29T10:44:08+00:00`
- Latest stored Braiins sample: `2026-04-29T10:39:07+00:00`
- Latest sample state: stale
- Latest report: `reports/run-20260504T075743Z-d828d0.md`
- Important interpretation: latest zero-sample reports are failed instrumentation, not market evidence

## Why The Engine Was Stopped

The running supervisor process was started before the latest reliability patch. It was still cooling down after zero-sample failed watch reports. That behavior is now fixed in code, but a live Python process does not reload edited code. The safe move before reboot is therefore:

1. Stop the old process.
2. Reboot.
3. Start the engine again from the patched code.

## Exact Human Steps After Reboot

Open Terminal and run:

```bash
cd /Users/oho/GitClone/CodexProjects/BraiinsRatchet
./scripts/ratchet engine status
./scripts/ratchet
./scripts/ratchet engine start
./scripts/ratchet app
```

Then stop touching it unless the app explicitly says otherwise.

Expected normal result:

- `engine status` first says not running.
- `./scripts/ratchet` probably says samples are stale.
- `engine start` starts the monitor-only forever supervisor.
- The app should show `ENGINE LIVE`.
- If Braiins/OCEAN fetching still fails, the patched engine should use short instrumentation retry backoff, not six-hour research cooldown.

## Exact Prompt To Give Codex After Reboot

```text
Continue the BraiinsRatchet project after reboot.
First read REBOOT_HANDOFF.md.
Then run:
  git status --short
  ./scripts/ratchet engine status
  ./scripts/ratchet
  ./scripts/ratchet app-state
Tell me the current state in plain English.
If the engine is stopped and there is no active manual exposure, start it with ./scripts/ratchet engine start.
Do not place Braiins orders. Do not touch files outside this repo.
Remember the branch is master, not main.
```

## Guardrails

- Monitor-only app. No Braiins owner-token actions.
- No containers or VMs.
- Modify only inside this repo.
- Treat runtime reports as evidence artifacts; do not stage them unless explicitly asked.
- If the computer reboot killed a process, do not recover by guessing. Restart from SQLite state using the commands above.
