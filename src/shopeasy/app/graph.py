from shopeasy.app.llm import get_model
from langgraph.graph import START, StateGraph, END
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from shopeasy.app.tools import get_order_status, get_all_orders, create_ticket, create_refund, rag_tool
from shopeasy.app.system_prompt import SYSTEM_PROMPT
from langgraph.prebuilt import ToolNode, tools_condition
import sqlite3

tools = [get_order_status, get_all_orders, create_ticket, create_refund, rag_tool]

llm = get_model()
llm_with_tools = llm.bind_tools(tools=tools)

class State(TypedDict):
    
    messages : Annotated[list[BaseMessage], add_messages]

def chat_node(state: State):

    messages = [
        SystemMessage(content= SYSTEM_PROMPT),
        *state["messages"]
    ]   
    res = llm_with_tools.invoke(messages)

    return {"messages": [res]}


connection = sqlite3.connect("checkpoints.sqlite", check_same_thread=False) 
checkpoint = SqliteSaver(conn=connection)

graph = StateGraph(State)
graph.add_node("chat", chat_node)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "chat")
graph.add_conditional_edges(
    "chat",
    tools_condition
)
graph.add_edge("tools", "chat")
chatbot = graph.compile(checkpointer= checkpoint)

config = {
    "configurable": {"customer_id": 1, "thread_id": "thread_01"}
}


# res = chatbot.invoke(
#             {"messages":[HumanMessage("list all of my orders i want to see them all")]},
#             config= config
#         )
# print(res["messages"][-1].content)

if __name__ == "__main__":
    while True:
        user_input = input("user: ")

        # print(f"user: {user_input}")

        if user_input.strip().lower() in ["quit", "bye", "exit"]:
            break

        ai_msg = chatbot.invoke(
            {"messages":[HumanMessage(content=user_input)]},
            config= config
            )

        print("ai: ", ai_msg["messages"][-1].content)