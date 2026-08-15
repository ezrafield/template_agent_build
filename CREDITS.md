# Credits And Open-Source Influences

This template grows by studying open-source projects that solve specific parts
of agent-assisted software development. The projects below shaped its design or
are recommended as optional tools.

## Design Influences

| Project | What this template learned or adopted | License |
| --- | --- | --- |
| [contextd](https://github.com/philngt/contextd) | Treat task context as a deterministic build artifact with explainable selection, omissions, budgets, and provenance. This template implements a smaller route-first Markdown compiler and does not depend on or vendor contextd. | MIT |
| [PlugMem](https://github.com/TIMAN-group/PlugMem) | The semantic, procedural, and episodic memory taxonomy; extracting compact reusable knowledge from verbose task history; and treating retrieval as input to reasoning rather than truth. This template implements a smaller Markdown-and-JSON workflow and does not depend on PlugMem. | Apache-2.0 |
| [RTK](https://github.com/rtk-ai/rtk) | Command output is part of the context budget. The template therefore prefers compact output for noisy commands, preserves failures, supports raw reruns, and keeps compression optional. | Apache-2.0 |
| [Semble](https://github.com/MinishLab/semble) | Natural-language retrieval can narrow likely source files before exact search and full-file reads. The template uses Semble as an optional retrieval layer and keeps `rg` as the exact confirmation step. | MIT |
| [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) | Code knowledge graphs can support architecture discovery, dependency reasoning, onboarding, and targeted graph search without making generated graph data part of normal repository context. | MIT |

## Optional Ecosystem Tools

| Project | Role in this template | License |
| --- | --- | --- |
| [Serena](https://github.com/oraios/serena) | Optional language-server-backed symbol navigation, references, diagnostics, and refactoring support. | MIT |
| [Repomix](https://github.com/yamadashy/repomix) | Optional repository bundling for external review; intentionally not the default daily retrieval workflow. | MIT |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Fast exact text, symbol, and path confirmation through `rg`. | Unlicense / MIT |

## Attribution Scope

This repository does not vendor source code from the projects above. References
to their names, commands, and workflows describe interoperability, optional
usage, or design influence. Each upstream project remains governed by its own
license, copyright notices, contribution rules, and trademarks.

License labels and repository links were verified on 2026-06-21. Consult the
upstream repositories for their current terms.

The contextd repository link and license were verified on 2026-08-15.

Thank you to the maintainers and contributors who make these ideas available
for others to study, test, and improve.
