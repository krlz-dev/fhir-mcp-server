"""
Servidor MCP mínimo sobre FHIR.

Consulta un servidor HAPI FHIR público de prueba (hapi.fhir.org) y expone
tres primitivas MCP: un tool, un resource y un prompt.

NUNCA usar datos clínicos reales acá. hapi.fhir.org es un sandbox público
con datos de prueba.

Correr:
    uv run mcp dev server.py        # inspector web
    uv run mcp run server.py        # stdio, para un host real
"""

import httpx

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

FHIR_BASE = "https://hapi.fhir.org/baseR4"
TIMEOUT = 20.0

mcp = MCPServer("FHIR Demo")


# ---------------------------------------------------------------- TOOL
# Lo llama el MODELO cuando decide que necesita buscar.
@mcp.tool()
async def search_patients(family_name: str, limit: int = 5) -> list[dict]:
    """Busca pacientes por apellido en el servidor FHIR."""
    params = {"family": family_name, "_count": limit}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{FHIR_BASE}/Patient", params=params)

    if r.status_code != 200:
        raise ToolError(f"El servidor FHIR respondió {r.status_code}")

    bundle = r.json()
    out: list[dict] = []
    for entry in bundle.get("entry", [])[:limit]:
        res = entry.get("resource", {})
        name = (res.get("name") or [{}])[0]
        out.append(
            {
                "id": res.get("id"),
                "family": name.get("family"),
                "given": " ".join(name.get("given", [])),
                "gender": res.get("gender"),
                "birth_date": res.get("birthDate"),
            }
        )
    return out


@mcp.tool()
async def get_observations(patient_id: str, limit: int = 10) -> list[dict]:
    """Trae las observaciones clínicas de un paciente por su ID FHIR."""
    params = {"patient": patient_id, "_count": limit}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{FHIR_BASE}/Observation", params=params)

    if r.status_code != 200:
        raise ToolError(f"El servidor FHIR respondió {r.status_code}")

    bundle = r.json()
    out: list[dict] = []
    for entry in bundle.get("entry", [])[:limit]:
        res = entry.get("resource", {})
        qty = res.get("valueQuantity") or {}
        out.append(
            {
                "id": res.get("id"),
                "code": (res.get("code", {}).get("coding") or [{}])[0].get("display"),
                "value": qty.get("value"),
                "unit": qty.get("unit"),
                "effective": res.get("effectiveDateTime"),
            }
        )
    return out


# ------------------------------------------------------------ RESOURCE
# Lo carga la APLICACIÓN al contexto. Es un GET: no cambia nada.
@mcp.resource("fhir://patient/{patient_id}")
async def patient_resource(patient_id: str) -> str:
    """Ficha de un paciente como texto plano."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{FHIR_BASE}/Patient/{patient_id}")

    if r.status_code != 200:
        return f"No se encontró el paciente {patient_id} (HTTP {r.status_code})"

    res = r.json()
    name = (res.get("name") or [{}])[0]
    return (
        f"Paciente {res.get('id')}\n"
        f"Nombre: {' '.join(name.get('given', []))} {name.get('family', '')}\n"
        f"Género: {res.get('gender')}\n"
        f"Nacimiento: {res.get('birthDate')}"
    )


# -------------------------------------------------------------- PROMPT
# Lo invoca el USUARIO por nombre, como un slash command.
@mcp.prompt()
def resumen_clinico(patient_id: str) -> str:
    """Plantilla para pedir un resumen clínico de un paciente."""
    return (
        f"Usá el resource fhir://patient/{patient_id} y el tool get_observations "
        f"para armar un resumen clínico breve del paciente {patient_id}. "
        f"Señalá explícitamente qué datos faltan en vez de inferirlos."
    )


if __name__ == "__main__":
    mcp.run()
