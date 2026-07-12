from typing import Annotated, TypedDict 
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_aws import ChatBedrockConverse

llm = ChatBedrockConverse(
    model = "us.anthropic.claude-sonnet-5",
    region_name = "us-east-1"
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return { "messages": [llm.invoke(state["messages"])] }

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

graph = builder.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "안녕, 넌 누구야?"}]})
print(result['messages'][-1].content)
