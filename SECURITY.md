# Security And Safety

This repository is designed to be monitor-only.

## Token Policy

- `BRAIINS_WATCHER_TOKEN` may be used for read-only API calls.
- Owner/admin Braiins tokens must never be passed to this code.
- `.env` is ignored by Git.
- The CLI refuses token values containing common owner/admin labels.

## Computer Safety

- No containers.
- No VMs.
- No writes outside this repository.
- No shelling out from package code.
- No destructive filesystem operations.

## Trading Safety

- Recommendations are not orders.
- Manual execution remains outside the program.
- Any future live executor must be reviewed as a separate change and disabled by default.

