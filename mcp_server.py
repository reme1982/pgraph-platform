# mcp_server.py - Exposes ecommerce.db via Model Context Protocol (MCP)
import sqlite3
import sys
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Inicializar el servidor MCP
server = Server("ecommerce-database")

def execute_query(sql: str) -> str:
    """Ejecuta una consulta SQL SELECT sobre la base de datos ecommerce.db."""
    # Validación de seguridad: solo permitir consultas SELECT
    clean_sql = sql.strip().upper()
    if not clean_sql.startswith("SELECT"):
        return json.dumps({"error": "Error de Seguridad: Solo se permiten consultas de tipo SELECT."})
        
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect("ecommerce.db")
        cursor = conn.cursor()
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # Obtener los nombres de las columnas
        columns = [desc[0] for desc in cursor.description]
        
        # Formatear el resultado como una lista de diccionarios
        result = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error al ejecutar la consulta SQL: {str(e)}"})

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista las herramientas disponibles en este servidor MCP."""
    return [
        Tool(
            name="query_ecommerce_db",
            description=(
                "Ejecuta consultas de solo lectura (SELECT) en la base de datos de comercio electrónico. "
                "Utilízala para obtener el historial de compras de los clientes, montos y fechas de transacción. "
                "Argumento esperado: sql_query (string)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "Consulta SQL SELECT completa a ejecutar (ej: SELECT * FROM purchases)"
                    }
                },
                "required": ["sql_query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Maneja la ejecución de las herramientas llamadas por el agente."""
    if name == "query_ecommerce_db":
        sql_query = arguments.get("sql_query")
        if not sql_query:
            return [TextContent(type="text", text="Error: Falta el argumento 'sql_query'.")]
            
        # Loggear el comando a stderr para no corromper stdio
        print(f"Ejecutando consulta MCP: {sql_query}", file=sys.stderr)
        
        result_str = execute_query(sql_query)
        return [TextContent(type="text", text=result_str)]
    else:
        return [TextContent(type="text", text=f"Error: Herramienta '{name}' no encontrada.")]

async def main():
    # El servidor stdio maneja la lectura de stdin y escritura en stdout
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
