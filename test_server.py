"""
Tests del servidor MCP, en memoria.

Client(mcp) se conecta directo al objeto servidor: sin subproceso, sin puerto,
sin red. Es la misma idea que TestClient de FastAPI.

Correr:
    pytest -v
"""

import pytest
from mcp import Client

from server import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with Client(mcp, raise_exceptions=True) as c:
        yield c


@pytest.mark.anyio
async def test_tools_registrados(client: Client):
    """El servidor expone los dos tools con el schema correcto."""
    tools = await client.list_tools()
    nombres = {t.name for t in tools.tools}
    assert nombres == {"search_patients", "get_observations"}

    search = next(t for t in tools.tools if t.name == "search_patients")
    props = search.input_schema["properties"]
    assert props["family_name"]["type"] == "string"
    # limit tiene default, así que no es requerido
    assert search.input_schema["required"] == ["family_name"]


@pytest.mark.anyio
async def test_prompt_registrado(client: Client):
    prompts = await client.list_prompts()
    assert {p.name for p in prompts.prompts} == {"resumen_clinico"}


@pytest.mark.anyio
async def test_resource_template(client: Client):
    tpl = await client.list_resource_templates()
    uris = {t.uri_template for t in tpl.resource_templates}
    assert "fhir://patient/{patient_id}" in uris


@pytest.mark.anyio
async def test_search_patients_contra_servidor_real(client: Client):
    """Test de integración: le pega al sandbox público de HAPI FHIR."""
    result = await client.call_tool("search_patients", {"family_name": "Smith", "limit": 3})
    assert result.is_error is False
    filas = result.structured_content["result"]
    assert isinstance(filas, list)
    if filas:  # el sandbox público puede estar vacío según el día
        assert "id" in filas[0]
