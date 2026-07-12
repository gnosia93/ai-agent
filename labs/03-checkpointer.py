"""
3장 - 메모리 (체크포인터)

상태 객체의 messages 데이터는 invoke 단위로 관리된다. 즉 아래와 같이 동작한다.

  result = graph.invoke({"messages": [{"role": "user", "content": "내 이름은 앨리스야"}]})
  # 이 invoke 안에서는 messages가 누적됨: [user, assistant]

  result2 = graph.invoke({"messages": [{"role": "user", "content": "내 이름 뭐야?"}]})
  # → LLM: "모르겠어요"  ← 앨리스를 기억 못 함!

add_messages는 "한 번의 대화 턴 안에서" 두뇌↔손발 핑퐁하며 쌓는 거고, 체크포인터는 "턴과 턴 사이"를 이어준다.
"""
from typing import Annotated, TypedDict 
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool 
from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition 

llm = ChatBedrockConverse(
    model = "us.anthropic.claude-sonnet-5",
#    temperature = 0, 
    region_name = "us-east-1",
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def agent(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

graph = builder.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "내 이름은 앨리스야"}]})
print(result["messages"][-1].content)

print("--" * 40)
result = graph.invoke({"messages": [{"role": "user", "content": "내 이름 뭐야?"}]})
print(result["messages"][-1].content)


print("--" * 40)
print("체코포인터 설정후 ...")
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = { "configurable": {"thread_id": "user-alice"} }

result = graph.invoke({"messages": [{"role": "user", "content": "내 이름은 앨리스야"}]}, config)
print(result["messages"][-1].content)

print("----" * 40)
result = graph.invoke({"messages": [{"role": "user", "content": "내 이름 뭐야?"}]}, config)
print(result["messages"][-1].content)
