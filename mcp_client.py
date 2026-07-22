import os
import sys
import asyncio
import certifi
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


_missing_keys = [
    name
    for name, value in {
        "TAVILY_API_KEY": TAVILY_API_KEY,
        "AVIATIONSTACK_API_KEY": AVIATION_STACK_API_KEY,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "GROQ_API_KEY": GROQ_API_KEY,
    }.items()
    if not value
]
if _missing_keys:
    raise ValueError(
        f"Missing required environment variables: {', '.join(_missing_keys)}. "
        "Please add them to your .env file."
    )


# LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)


client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },

        "aviationstack": {
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "aviationstack-mcp"
            ],
            "env": {
                "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY
            }
        },

        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                str(Path(__file__).parent / "custom_weather_mcp_server.py")
            ],
            "env": {
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY
            }
        }

        

        

    }

)




# Check if the client is connected to all servers
async def get_all_tools():

    tools = await client.get_tools()

    print("\nAvailable MCP Tools:\n")

    for tool in tools:
        print(tool.name)




###################################
# MCP Tool Cache
###################################
# All MCP tools (Tavily, AviationStack, Weather) are fetched once and cached
# by name in a single dict, then invoked through one generic caller.

mcp_tools = {}


async def initialize_mcp():
    global mcp_tools

    if mcp_tools:
        return

    tools = await client.get_tools()

    print("\nAvailable MCP Tools:\n")
    for tool in tools:
        print(tool.name)

    mcp_tools = {tool.name: tool for tool in tools}


async def call_mcp_tool(tool_name: str, tool_args: dict = None):
    await initialize_mcp()
    tool = mcp_tools[tool_name]
    return await tool.ainvoke(tool_args or {})




async def tavily_mcp_search(query: str):
    return await call_mcp_tool("tavily_search", {"query": query})


async def aviation_mcp_call(tool_name: str, tool_args: dict = None):
    return await call_mcp_tool(tool_name, tool_args)


async def weather_mcp_search(city: str):
    return await call_mcp_tool("get_current_weather", {"city": city})


async def forecast_mcp_search(city: str):
    return await call_mcp_tool("get_forecast", {"city": city})




###################################
# Destination Extractor
###################################

async def extract_destination(query: str):

    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = await llm.ainvoke(prompt)

    return response.content.strip()


