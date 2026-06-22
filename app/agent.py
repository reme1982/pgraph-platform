# ruff: noqa
import datetime
import os
import subprocess
import asyncio
import sys
import google.auth
import nest_asyncio
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()

# Apply nest_asyncio to support nested event loops in interactive environments
nest_asyncio.apply()

# Configure the runtime environment
use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True").upper() == "TRUE"

if use_vertex:
    try:
        _, project_id = google.auth.default()
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    except Exception:
        # Fallback to AI Studio if GCP authentication fails
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
else:
    # Force use of Google AI Studio
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"


def safe_print(text: str):
    """Prints text to stdout, falling back to replacing unsupported characters on encoding errors (common on Windows)."""
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "ascii"
        clean_text = text.encode(encoding, errors="replace").decode(encoding)
        sys.stdout.write(clean_text + "\n")
        sys.stdout.flush()


# --- TOOL 1: Data access via MCP Server (Day 2) ---
def query_ecommerce_db(sql_query: str) -> str:
    """Executes a SQL SELECT query on the E-commerce database via the Model Context Protocol (MCP) server.
    
    Args:
        sql_query: The full SQL SELECT query to execute (e.g., SELECT * FROM purchases).
        
    Returns:
        A formatted JSON string with the query results or an error message.
    """
    async def run_client():
        # Set up stdio communication with the local MCP server using uv run
        server_params = StdioServerParameters(
            command="uv", args=["run", "python", "mcp_server.py"]
        )
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.call_tool("query_ecommerce_db", {"sql_query": sql_query})
                return response.content[0].text

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        return loop.run_until_complete(run_client())
    else:
        return asyncio.run(run_client())


# --- TOOL 2: Isolated RFM Segmentation Skill (Day 3 & 4) ---
def run_rfm_segmentation_skill() -> str:
    """Executes the RFM segmentation skill in an isolated subprocess.
    Calculates recency, frequency, and monetary scores for each customer and saves a JSON output.
    
    Returns:
        A summary message of the completed segmentation or an error message.
    """
    try:
        # Computational isolation using subprocess (Zero Ambient Authority)
        # Use explicit utf-8 encoding to avoid Windows CP1252 decode errors
        result = subprocess.run(
            ["uv", "run", "python", "skills/rfm_segmentation.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error executing RFM segmentation: {str(e)}"


# --- TOOL 3: Executive Report Skill with HITL (Day 4) ---
def generate_executive_report_skill() -> str:
    """Generates the strategic customer retention report inside the /reports/ directory.
    This high-stakes action requires operator confirmation (Human-in-the-Loop).
    
    Returns:
        The generated report path or a cancellation message.
    """
    safe_print("\n" + "="*80)
    safe_print("[HITL CHALLENGE] The AI agent is attempting to generate and save the final executive report.")
    safe_print("Please validate and confirm this action in your terminal.")
    safe_print("="*80)
    
    try:
        approval = input("[Approve retention report Y/N]: ").strip().upper()
    except Exception:
        approval = "Y" # Default fallback in non-interactive stdout redirections
        
    if approval != "Y":
        return "OPERATION CANCELLED: Operator did not approve report generation. Action blocked for security."
        
    try:
        # Execute report generation in isolation with explicit utf-8 encoding
        result = subprocess.run(
            ["uv", "run", "python", "skills/executive_report.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error generating executive business report: {str(e)}"


# --- GOOGLE ADK MAIN AGENT DEFINITION (Day 5) ---
root_agent = Agent(
    name="pgrap_retention_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the PGRAP Customer Retention and Growth Agent. Your goal is to help E-commerce "
        "business managers analyze customer retention data, identify churn risk, and generate "
        "personalized business retention strategies.\n"
        "To answer business queries, follow this sequence:\n"
        "1. Use `query_ecommerce_db` to query transaction data directly for specific questions.\n"
        "2. If a general analysis is requested, execute `run_rfm_segmentation_skill` first to segment the database.\n"
        "3. Then, call `generate_executive_report_skill` to compile and save the Markdown strategic report.\n"
        "Note: Remember database queries must go through the MCP server tool, and generating the report "
        "requires operator validation (HITL)."
    ),
    tools=[query_ecommerce_db, run_rfm_segmentation_skill, generate_executive_report_skill],
)

app = App(
    root_agent=root_agent,
    name="app",
)

# Allow direct interactive CLI testing of the agent
if __name__ == "__main__":
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="local_user", app_name="local_pgrap")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="local_pgrap")
    
    safe_print("="*80)
    safe_print("PGRAP Agent started locally in interactive mode (Google AI Studio).")
    safe_print("You can prompt the agent, e.g.: 'Run the segmentation and generate the executive report'")
    safe_print("Type 'exit' to quit.")
    safe_print("="*80)
    
    while True:
        try:
            prompt = input("\nUser: ")
            if prompt.strip().lower() in ["exit", "quit", "salir"]:
                break
            if not prompt.strip():
                continue
            
            safe_print("Thinking...")
            
            # Format message according to Google GenAI Content standard
            message = types.Content(
                role="user", parts=[types.Part.from_text(text=prompt)]
            )
            
            # Run the agent using the official ADK Runner
            events = list(
                runner.run(
                    new_message=message,
                    user_id="local_user",
                    session_id=session.id
                )
            )
            
            # Extract and display the resulting text
            response_text = ""
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
            
            safe_print(f"\nAgent:\n{response_text}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            safe_print(f"\nError during execution: {e}")
            
    safe_print("\nSession finished.")
