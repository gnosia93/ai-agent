from typing import Annotated, TypedDict 
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool 
from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition 

@tool
def multiply(a: int, b: int) -> int:
    """두 정수를 곱한다"""
    return a * b

tools = [multiply]

llm = ChatBedrockConverse(
    model = "us.anthropic.claude-sonnet-5",
#    temperature = 0, 
    region_name = "us-east-1",
).bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def agent(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()
result = graph.invoke(
    { 
        "messages": [ 
            { 
                "role": "user", 
                "content": "23 곱하기 17은 ?"
            } 
        ]
    })

print(result["messages"][-1].content)


def create_graph():
    # 그래프 이미지 파일 생성
    png = graph.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png)

create_graph()


"""
 전체 흐름

  1. START → agent      : LLM에게 질문 전달
  2. agent 실행          : LLM이 "날씨 도구 불러야겠다" 결정
  3. tools_condition 판단 : 도구 호출 있음 → "tools"로
  4. tools 실행          : 실제로 날씨 조회
  5. tools → agent       : 결과를 LLM에게 되돌림
  6. agent 실행          : LLM이 결과 보고 "이제 답할 수 있다"
  7. tools_condition 판단 : 도구 호출 없음 → END
  8. 끝                  : 최종 답변
"""

"""
LangGraph 에이전트는 "안에서 뭐가 도는지" 안 보이면 진짜 답답하죠 (아까 tool_runner
  때랑 같은 갈증 ㅎㅎ). 방법이 여러 겹이에요 — 가벼운 것부터.

  1. 제일 가벼움 — stream()으로 단계별 출력

  invoke()(결과만) 대신 stream()을 쓰면 노드가 실행될 때마다 중간 상태가 나와요:

  for chunk in graph.stream(
      {"messages": [{"role": "user", "content": "서울 날씨 어때?"}]},
      stream_mode="updates",     # 각 노드가 뭘 바꿨는지
  ):
      print(chunk)
      print("─" * 40)

  agent가 도구 부르는 순간, tools가 실행되는 순간이 순서대로 찍혀요. START→agent→tools→agent→END 흐름이
  눈에 보입니다.

  stream_mode 옵션:
  - "updates" — 각 노드가 만든 변경분만 (제일 읽기 좋음)
  - "values" — 매 단계 전체 state
  - "debug" — 가장 상세 (노드 진입/종료, 태스크까지)

  2. 메시지 예쁘게 — pretty_print()

  stream으로 받은 메시지를 보기 좋게:

  for chunk in graph.stream(inputs, stream_mode="values"):
      chunk["messages"][-1].pretty_print()

  도구 호출(tool_calls), 도구 결과가 각각 구분되어 출력돼요. LLM이 어떤 인자로 도구를 불렀는지까지
  보여서 디버깅에 최고예요.

  3. 전체 자동 로깅 — 디버그 모드

  컴파일할 때 켜면 모든 단계가 자동으로 찍혀요:

  graph = builder.compile(debug=True)
  result = graph.invoke(inputs)   # 실행하면 알아서 상세 로그가 나옴

  4. 제대로 된 트레이싱 — LangSmith (강력 추천)

  여러 번 호출·중첩·도구 루프가 복잡해지면 텍스트 로그로는 한계가 와요. LangSmith는 LangChain 팀이 만든
  트레이싱 도구인데, 웹 UI에서 각 노드·LLM 호출·토큰·소요시간을 트리로 보여줘요:

  pip install langsmith

  import os
  os.environ["LANGSMITH_TRACING"] = "true"
  os.environ["LANGSMITH_API_KEY"] = "lsv2_..."   # smith.langchain.com에서 발급
  os.environ["LANGSMITH_PROJECT"] = "my-agent"   # 선택

  이 환경변수만 켜두면 코드는 한 줄도 안 바꿔도 모든 실행이 자동으로 웹에 기록돼요. 어느 노드에서
  느린지, LLM이 뭘 받고 뭘 뱉었는지 전부 클릭해서 볼 수 있어요.

  ⚠️ 단, LangSmith는 외부 서비스로 데이터가 전송돼요 (프롬프트·응답이 클라우드에 저장됨). 민감한
  데이터면 이 점 확인하고 쓰세요.

  5. 로컬 완전 커스텀 — 콜백

  외부 전송 없이 직접 훅을 걸고 싶으면:

  from langchain_core.callbacks import BaseCallbackHandler

  class TraceHandler(BaseCallbackHandler):
      def on_llm_start(self, serialized, prompts, **kwargs):
          print(f"🧠 LLM 호출 시작")
      def on_tool_start(self, serialized, input_str, **kwargs):
          print(f"🔧 도구 실행: {input_str}")
      def on_tool_end(self, output, **kwargs):
          print(f"   ↳ 결과: {output}")

  result = graph.invoke(inputs, config={"callbacks": [TraceHandler()]})

  정리 / 추천 순서

  ┌──────────────────────────────┬──────────────────────────────────────────┐
  │             상황             │                   방법                   │
  ├──────────────────────────────┼──────────────────────────────────────────┤
  │ 그냥 흐름만 빨리 보기        │ stream(stream_mode="updates") ← 여기부터 │
  ├──────────────────────────────┼──────────────────────────────────────────┤
  │ 도구 호출 인자까지 예쁘게    │ pretty_print()                           │
  ├──────────────────────────────┼──────────────────────────────────────────┤
  │ 다 자동으로 찍기             │ compile(debug=True)                      │
  ├──────────────────────────────┼──────────────────────────────────────────┤
  │ 복잡해졌다, 웹 UI로 보고싶다 │ LangSmith (외부 전송 주의)               │
  ├──────────────────────────────┼──────────────────────────────────────────┤
  │ 외부 전송 없이 커스텀 훅     │ 콜백 핸들러                              │
  └──────────────────────────────┴──────────────────────────────────────────┘

  지금 단계면 1번(stream)부터 시작하세요. 터미널에서 바로 흐름이 보여서, 아까 궁금해하던
  tools_condition이 실제로 어디로 분기하는지도 눈으로 확인돼요.

  ---
  어떤 걸 써볼까요? stream으로 실제 출력이 어떻게 나오는지 예시를 더 자세히 보여드릴 수도 있고,
  LangSmith 셋업을 같이 해볼 수도 있어요.
"""

for chunk in graph.stream(
    {"messages": [{"role": "user", "content": "23 곱하기 17은 ?"}]},
    stream_mode="updates",     # 각 노드가 뭘 바꿨는지
):
    print(chunk)
    print("─" * 40)

for chunk in graph.stream(
    {"messages": [{"role": "user", "content": "23 곱하기 17은 ?"}]}, 
    stream_mode="values"
):
    chunk["messages"][-1].pretty_print()



"""
"LLM으로 나가는 요청(도구 스키마가 실린 그 페이로드)을 실제로 보고 싶다"는 거죠? 방금 얘기한 tools
  필드가 진짜로 어떻게 나가는지요. 몇 가지 방법이 있어요.

  1. 가장 쉬움 — LangChain 전역 디버그

  한 줄이면 모든 LLM 요청/응답의 raw 페이로드가 콘솔에 찍혀요:

  from langchain.globals import set_debug
  set_debug(True)

  # 이제 아무 호출이나 하면 전부 출력됨
  result = graph.invoke(inputs)

  여기서 LLM으로 나가는 messages, tools 필드, 돌아온 tool_calls까지 다 보여요. 방금 궁금해하던 "도구가
  별도 필드로 나가는" 그 모습이 실제로 찍힙니다.

  set_debug가 너무 시끄러우면 한 단계 약한 버전:
  from langchain.globals import set_verbose
  set_verbose(True)   # 좀 더 정리된 출력

  2. 요청 payload만 콕 집어 보기

  전역 디버그가 과하면, 도구 바인딩된 결과를 직접 뜯어봐요:

  llm_with_tools = llm.bind_tools(tools)

  # LLM에 실제로 전달될 도구 스키마 확인
  import json
  print(json.dumps(llm_with_tools.kwargs["tools"], indent=2, ensure_ascii=False))

  이러면 get_weather가 어떤 JSON 스키마로 변환돼서 나가는지 그대로 보여요.

  3. "스트림"이 응답 토큰 스트리밍이라면

  혹시 LLM이 답을 뱉는 걸 실시간 토큰 단위로 보고 싶은 거라면 (요청이 아니라 응답 쪽):

  for chunk in graph.stream(
      {"messages": [{"role": "user", "content": "서울 날씨?"}]},
      stream_mode="messages",     # ← LLM 토큰을 실시간으로
  ):
      print(chunk, end="", flush=True)

  stream_mode="messages"는 LLM이 생성하는 토큰을 흘러나오는 대로 출력해요.

  4. raw HTTP 레벨까지 — boto3 로깅

  Bedrock으로 실제 나가는 HTTP 요청 자체를 보고 싶으면 (가장 낮은 레벨):

  import logging
  import boto3

  boto3.set_stream_logger("", logging.DEBUG)

  ⚠️ 이건 매우 시끄러워요. AWS 서명·헤더·전체 body가 다 찍혀서, 정말 저수준 디버깅 아니면 비추. 1번으로
  대부분 해결돼요.

  정리 / 추천

  ┌───────────────────────────────┬────────────────────────────────────┐
  │         보고 싶은 것          │                방법                │
  ├───────────────────────────────┼────────────────────────────────────┤
  │ 나가는 요청 전체 (tools 포함) │ set_debug(True) ← 여기부터         │
  ├───────────────────────────────┼────────────────────────────────────┤
  │ 도구 스키마만 콕              │ llm_with_tools.kwargs["tools"]     │
  ├───────────────────────────────┼────────────────────────────────────┤
  │ LLM 응답 토큰 실시간          │ stream(stream_mode="messages")     │
  ├───────────────────────────────┼────────────────────────────────────┤
  │ HTTP raw까지                  │ boto3.set_stream_logger (시끄러움) │
  └───────────────────────────────┴────────────────────────────────────┘

  지금 궁금한 게 "도구가 어떻게 실려 나가나"라면 set_debug(True) 한 줄이 딱이에요. 방금 우리가 말로
  설명한 tools 필드가 실물로 찍혀서, 개념이 코드로 확인돼요.

  ---
  어떤 "스트림"을 말씀하신 거였어요? 나가는 요청(도구 스키마)인지, 들어오는 응답 토큰인지에 따라
  1번이냐 3번이냐 갈려서요. 확실히 해주시면 그쪽으로 예시를 더 풀어드릴게요.
"""

