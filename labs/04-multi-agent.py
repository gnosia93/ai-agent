from typing import Annotated, Literal, TypedDict
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages 
from langchain.agents import create_agent

llm = ChatBedrockConverse(
    model = "us.anthropic.claude-sonnet-5",
    region_name = "us-east-1", 
)

@tool
def add(a: int, b: int) -> int:
    """두 수를 더합니다."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """두 수를 곱합니다."""
    return a * b

@tool
def web_search(query: str) -> str:
    """웹에서 정보를 검색한다. (여기서는 예제용 가짜 검색)"""
    
    # 실제로는 Travily, SerpAPI 등을 사용한다. 
    fake_db = {
        "대한민국 수도": "대한민국의 수도는 서울이다. 인구는 약 940만 명이다.",
        "서울 인구": "서울의 인구는 약 940만 명이다.",
        "프랑스 수도": "프랑스의 수도는 파리다.",
    }
    
    for key, value in fake_db.items():
         if key in query or query in key:
             return value
    
    return f"'{query}' 에 대한 검색 결과를 찾지 못했다."

math_agent = create_agent(
    llm,
    tools = [multiply, add],
    system_prompt = "너는 계산 전문가다. 주어진 도구만 써서 정확히 계산하고 결과를 한글로 답한다."
)

research_agent = create_agent(
    llm,
    tools = [web_search],
    system_prompt = "너는 조사 전문가다. web_search 도구로 사실을 찾아 한국어로 답한다."
)

# 수퍼바이저
