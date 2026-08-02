# Architecture

## Components

| Component | Responsibility | Trust boundary |
|---|---|---|
| `envi_classic_mcp` | ENVI discovery, process ownership, Win32 menus, constrained GUI actions, evidence capture | Only processes launched by this server |
| `envi-classic-lab-automation` | Guide-derived stage planning, orchestration and evidence gating | Cannot waive a frozen stage |
| `remote-sensing-report` | Template-based report writing and DOCX/PDF verification | Reads validated evidence; does not invent results |

## Session lifecycle

1. `envi_classic_health_check`
2. `envi_classic_launch`
3. `envi_classic_register_inputs`
4. `envi_classic_set_stage_plan`
5. menu discovery, controlled GUI actions and `envi_classic_capture_evidence`
6. `envi_classic_register_output`
7. `envi_classic_finalize_evidence`
8. report generation only when `complete=true`
9. `envi_classic_close_session`

Every mutable operation is scoped to a server-owned session. Screenshot and output paths are required to remain under the experiment workspace. The server intentionally exposes no generic shell, IDL or Python execution tool.
