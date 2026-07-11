from typing import TypedDict 
from langgraph.graph import StateGraph, START, END
from anthropic import AnthropicBedrockMantle 

client = AnthropicBedrockMantle(aws_region='us-east-1')

class State(TypedDict):
    count: int
    question : str
    answer : str

def increment(state: State):
    return { "count": state["count"] + 1 }

def ask_claude(state: State):
    response = client.messages.create(
        model = "anthropic.claude-opus-4-8",
        max_tokens = 1024,
        messages = [{"role": "user", "content": state["question"]}],
    )
    text = next((b.text for b in response.content if b.type == 'text'), "")

    return {"answer": text}
 
builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_node("ask_claude", ask_claude)
builder.add_edge(START, "increment")
builder.add_edge("increment", "ask_claude")
builder.add_edge("ask_claude", END)

graph = builder.compile()

result = graph.invoke({"count": 0, "question": '프랑스의 수도는?'})
print(result)
