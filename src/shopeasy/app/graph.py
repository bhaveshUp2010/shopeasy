from shopeasy.app.llm import get_model
from langgraph.graph import START, StateGraph, END
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

llm = get_model()


class State(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]

def chat_node(state: State):

    messages = [
        SystemMessage("""You are an AI customer support assistant for an e-commerce company.

Your responsibilities are to help customers with:
- Order details and delivery status.
- Refund queries and refund requests.
- Creating and tracking support tickets.
- General customer complaints and queries.

**Guidelines:**
1. Be friendly, professional, empathetic, and concise.
2. Always verify customer ownership before sharing order information.
3. Never invent customer details, order statuses, or refund information.
4. Check refund eligibility before initiating a refund.
5. Never claim an action succeeded unless the corresponding tool or database operation confirms it.
6. Ask for missing information when necessary.
7. Never expose customer data to unauthorized users.
8. If an issue cannot be resolved, offer to create a support ticket.

Prioritize customer privacy, accuracy, and helpfulness in every interaction."""),
        *state["messages"]
    ]   
    res = llm.invoke(messages)

    return {"messages": [res]}

graph = StateGraph(State)

graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile()

while True:
    user_input = input("user: ")

    # print(f"user: {user_input}")

    if user_input.strip().lower() in ["quit", "bye", "exit"]:
        break

    print("ai: ", end = " ", flush= True)
    for message_chunk, metadata in chatbot.stream(
        {"messages": [HumanMessage(content=user_input)]},
        stream_mode="messages",
    ):
        if message_chunk.content:
            print( message_chunk.content, end= " ", flush= True)       
    print() 