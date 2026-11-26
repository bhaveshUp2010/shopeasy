import asyncio
from shopeasy.app.mcp.client import client
from shopeasy.app.agent.graph import build_graph
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

async def main():

    model = ChatGroq(model = "openai/gpt-oss-120b")
    config = {
        "configurable": {"thread_id": "002", "customer_id": "1"}
    }

    async with client() as tools:
        print("Discovered Tools: ")
        for tool in tools:
            print(tool.name)

        graph = build_graph(model, tools)

        response = await graph.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Show me my profile"
                    }
                ]
            },
            config=config
        )

        print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())