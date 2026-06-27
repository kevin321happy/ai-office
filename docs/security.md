# Security and Privacy Rules

AI Office is intended to be a personal GitHub project and must not contain private company data.

## Commit Gate

Run this before every commit:

```bash
./scripts/privacy_scan.sh
git status --short
git diff --cached --stat
```

## Never Commit

- Company names, aliases, logos, internal identifiers, or any private organization markers.
- Internal repository paths.
- Real TAPD, GitLab, Jenkins, or DingTalk URLs and credentials.
- Tokens, webhooks, cookies, passwords, private keys, or local secret config.
- Real work tasks, MR diffs, crash logs, reports, or knowledge base files.
- Customer names, tenant names, package names, or production identifiers.

## Local Only

These directories are ignored and must remain local:

```text
tasks/
knowledge/
logs/
reports/
```

## Public Examples

Use simulated data in public examples. Keep real settings in local files such as:

```text
config/config.local.json
config/privacy_patterns.local.txt
.env
```

Keep organization-specific privacy patterns in `config/privacy_patterns.local.txt`. This file is ignored by git and used only by the local privacy scanner.
