# Editor MCP setup (Unreal MCP in the editor)

Agents can work on levels, Blueprints and materials in the editor through Epic's Unreal MCP server
(`docs/unreal-sources.md` U25, `pipeline/unreal-rules.md` "Agents driving the editor through MCP").
Official Rules §7(h) allows "agent configurations, Model Context Protocol ("MCP") settings" to be prepared before
the Contest Period, so this config is pre-jam work. Levels, Blueprints and materials made with it are game content
and are made during the jam.

## Files
- `pipeline/agent-ops/mcp.template.json`: the `.mcp.json` the team turns on. Server names and commands carry
  [VERIFY on 5.8.4] until card 0.4a pastes the editor's output (the template's `_verify` list).
- `pipeline/agent-ops/gates.json`: `mcp_enabled`, `mcp_roles`, `mcp_allow`, `mcp_ask_words`. `pipeline/agent-ops/hook.py` enforces them.
- `tools/editor_mcp.py check`: validates the template, the gates and `.mcp.json` (CI runs it).

## Guardrails
1. Off by default. No `.mcp.json` and `mcp_enabled: false`: the hook blocks every `mcp__` call.
2. Only these roles: Level Designer, Integrator, Art Director, Asset Specialist, UI and UX (`mcp_roles`). Any other `JAM_ROLE` is blocked.
3. A card lane and a PR. A call off a card branch `ue-<id>-<name>` (or on `main`) is blocked. Lane, lock and save rules: `pipeline/unreal-rules.md`.
4. A human opens every changed asset. A PR that changes a `.uasset` or `.umap` needs
   `EDITOR CHECK: by=<the card's human> opened=<path>[,<path>] ok` under Evidence (`tools/check_pr.py` rule editor).
5. Tools that run Python or console commands always ask a human (`mcp_ask_words`). Unlisted tools are blocked (`mcp_allow`).

## Turning it on at kickoff (needs-human checkpoint)
Who: the TD human, with the team's OK at kickoff. One PR (gate files):
1. The editor runs the server; `ModelContextProtocol.GenerateClientConfig ClaudeCode` writes `.mcp.json`. It must match
   `mcpServers` in the template (`tools/editor_mcp.py check` fails otherwise).
2. `gates.json`: `mcp_enabled: true`, and the card 0.4a tool names in `mcp_allow`.
3. The line below is filled in, with a link to the kickoff comment.
4. The same switch turns on the art-tool servers (GIMP, Aseprite, Blender: `mcp.tools.template.json`, Codex format
   `codex-mcp.template.toml`). `tools/kickoff.sh` then hands each session only its role's servers, for Claude Code
   (`--mcp-config`) and Codex (`-c mcp_servers...`) alike (`tools/mcp_config.py`); `tools/kickoff.sh --check` shows
   whether each one answers.

Kickoff record: TBD
