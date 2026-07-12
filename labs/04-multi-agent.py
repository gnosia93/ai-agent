from typing import Annotated, Literal, TypedDict
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages 
from langgraph.prebuilt import create_react_agent

llm = ChatBedrockConverse(
    model = "us.anthropic.claude-sonnet-5",
    region_name = "us-east-1", 
)

@tool
def mutiply(a: int, b: int) -> int:
    """두 수를 곱합니다."""
    return a * b

