# fhir-mcp-server

A minimal [MCP](https://modelcontextprotocol.io) server over FHIR, built with the
**official Python SDK v2** (`mcp` 2.1.1+).

It exposes all three MCP primitives — tool, resource and prompt — against a
HAPI FHIR R4 server, and ships with an in-memory test suite.

The interesting problem with agent tooling isn't getting it to run once. It's
proving it behaves. So the tests are the point of this repo as much as the
server is.

## Why v2 matters

Most MCP tutorials and Stack Overflow answers still show the v1 API:

```python
from mcp.server.fastmcp import FastMCP   # v1 — outdated
from mcp.server import MCPServer         # v2 — current
```

SDK v2 was a major rework released alongside the 2026-07-28 spec revision. Two
things bite if you arrive from v1:

- Result models use `snake_case`: `tool.input_schema`, not `tool.inputSchema`;
  `result.resource_templates`, not `result.resourceTemplates`.
- `FastMCP` is gone from the official SDK. (Note: `fastmcp` on PyPI is a
  *different*, third-party package — don't confuse the two.)

## Requirements

Python 3.10+ and [uv](https://docs.astral.sh/uv/).

## Install

```bash
uv venv .venv
source .venv/bin/activate
uv pip install "mcp[cli]" httpx
uv pip install pytest inline-snapshot   # tests only
```

## Run

```bash
uv run mcp dev server.py     # MCP Inspector — try the tools in a form
uv run mcp run server.py     # stdio — for a real host
```

To connect it to a host (Claude Code, Claude Desktop, an IDE):

```bash
uv run --with "mcp[cli]" mcp run /absolute/path/to/server.py
```

The host launches the server as a subprocess and speaks over stdin/stdout.
No port, nothing listening on the network.

## Test

```bash
pytest -v
```

```
test_tools_registrados PASSED
test_prompt_registrado PASSED
test_resource_template PASSED
test_search_patients_contra_servidor_real PASSED
```

`Client(mcp)` connects to the server object **in memory** — no subprocess, no
port, no wire. Same idea as FastAPI's `TestClient`. The last test is an
integration test and hits the public sandbox, so it needs network.

## What it exposes

| Primitive | Name | Who triggers it |
|---|---|---|
| Tool | `search_patients(family_name, limit=5)` | the model |
| Tool | `get_observations(patient_id, limit=10)` | the model |
| Resource | `fhir://patient/{patient_id}` | the application |
| Prompt | `resumen_clinico(patient_id)` | the user |

The three primitives differ by **who decides to use them**, not by what they
do. A tool is a `POST` (acts, has side effects), a resource is a `GET` (loads
data, changes nothing), a prompt is a slash command.

You don't write JSON Schema — the SDK generates it from type hints. A
parameter with a default stops being required. It's just Python.

## Data

Points at `https://hapi.fhir.org/baseR4`, the public HAPI FHIR **test
sandbox**.

⚠️ **Never put real clinical data in a public repo.** Synthetic or sandbox
data, always.

## License

MIT

---

If this saved you an afternoon, [a coffee helps](https://buymeacoffee.com/krlz) ☕
