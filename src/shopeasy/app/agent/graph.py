from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Literal
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from shopeasy.app.agent.system_prompt import PROMPT
from pathlib import Path
import aiosqlite
CHECKPOINT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "checkpoint.sqlite"


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def build_graph(model, tools):

    conn = aiosqlite.connect(CHECKPOINT_PATH, check_same_thread= False)
    checkpointer = AsyncSqliteSaver(conn)
    model_with_tols = model.bind_tools(tools)

    async def agent_node(state: State):

        messages = [
            SystemMessage(PROMPT),
            *state["messages"]
        ]
        response = await model_with_tols.ainvoke(
            messages
        )

        return {
            "messages": [response]
        }

    workflow = StateGraph(State)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent", 
        tools_condition
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer= checkpointer)
