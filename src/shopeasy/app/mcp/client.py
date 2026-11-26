from contextlib import asynccontextmanager
import asyncio
from langchain.mcp import MCPAdapter

@asynccontextmanager
async def client():

    async with MCPAdapter(
        {
            "shopeasy": {
                "transport": "stdio",
                "command": "uv",
                "args": [
                    "run",
                    "python",
                    "-m",
                    "shopeasy.app.mcp.server",
                ],
            }
        }
    ) as adapter:

        tools = await adapter.list_tools()
        yield tools


if __name__ == "__main__":
    asyncio.run(client())
