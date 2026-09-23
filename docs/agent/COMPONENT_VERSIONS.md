# Component Versions

Snapshot: **2026-09-23**, reference kit and local Windows checkout. Upstream
versions below are dated observations, not automatically tested upgrade targets.

| Component | Kit requirement or pin | Observed locally | Upstream at audit |
| --- | --- | --- | --- |
| Repository identities | Kit **0.5.0**; sample application and tool wrapper **0.1.0** | Same separate identities | Repository-owned versions |
| Python | Core `>=3.11`; CI 3.11; optional tools `>=3.11,<3.14`, bootstrap 3.13 | Core 3.14.5; tools 3.13.13 | [3.14.7, 3.13.15, 3.11.16](https://www.python.org/downloads/) |
| Node.js | `>=22`; CI 22 | 24.16.0 | [24.21.0 LTS](https://nodejs.org/en/blog/release/v24.21.0); [26.10.0 Current](https://nodejs.org/en/about/previous-releases) |
| Codex CLI | Manifest/CI 0.146.0 | 0.154.0-alpha.6.1 | [0.156.0](https://learn.chatgpt.com/docs/changelog) |
| Semble | 0.4.1; pathspec 1.1.1 | Matches lock | [0.6.0](https://pypi.org/project/semble/) |
| Serena | 1.5.3; pathspec 0.12.1 | Matches lock | [1.7.0](https://pypi.org/project/serena-agent/) |
| ast-grep | 0.44.0 | Matches lock | [0.45.3 GitHub release](https://github.com/ast-grep/ast-grep/releases/tag/0.45.3); npm tag unverified |
| Repomix | **1.18.1**, updated from 1.16.0 | Manifest, lock, installation, and wrapper agree | [1.18.1 security fix](https://github.com/yamadashy/repomix/security/advisories/GHSA-4p5g-gh74-q524) |
| RTK | v0.43.0, per-platform archive SHA-256 pins | 0.43.0; cached Windows archive matches pin | [v0.49.0](https://github.com/rtk-ai/rtk/releases/tag/v0.49.0) |
| Jev shadow model | jev-1.13.0 | No live call | [jev-1.13.0](https://docs.typesafe.ai/models) |

Pins are authoritative in [the kit manifest](../../agentkit-manifest.json),
[Node manifest](../../tools/agent/package.json), its lock, the separate
[Python tool environments](../../tools/agent/python/), and
[RTK manifest](../../tools/agent/rtk-manifest.json). Installed metadata and
version commands establish the local column, not cross-platform compatibility.
The local unpinned `uv` prerequisite was 0.11.17; its upstream freshness was not audited.

Repomix passed local and clean temporary installs plus synthetic export checks
on Windows/Node 24.16.0. npm audit reported zero findings after the update.
Linux, Node 22, and signed-commit GPG behavior were not tested. Historical evidence
is kept in the reference checkout's `.agent/plans/completed/` records; those
project-owned records are not installed into another project.

For future updates, change one tool at a time, refresh its lock/checksums, and
verify its wrapper and relevant behavior. Keep Python tool environments isolated;
reconcile the Codex CI pin with a tested stable workstation version. Live model
comparisons stay explicit under the [evaluation guide](RELIABILITY_EVALS.md).
