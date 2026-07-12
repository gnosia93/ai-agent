---
  2단계: 도구 호출 + 조건 분기 (진짜 "에이전트")

  에이전트의 본질은 "LLM이 도구를 쓸지 말지 스스로 판단하고, 필요하면 반복하는 루프" 입니다. 그림으로:

  START → agent → (도구 필요?) → tools → agent → ... → (아니오) → END

  from typing import Annotated, TypedDict
  from langchain_anthropic import ChatAnthropic
  from langchain_core.tools import tool
  from langgraph.graph import StateGraph, START, END
  from langgraph.graph.message import add_messages
  from langgraph.prebuilt import ToolNode, tools_condition

  # 1. 도구 정의
  @tool
  def multiply(a: int, b: int) -> int:
      """두 정수를 곱한다."""
      return a * b

  tools = [multiply]

  # 2. LLM에 도구를 "바인딩" — 이제 LLM이 도구 호출을 반환할 수 있음
  llm = ChatAnthropic(model="claude-sonnet-5", temperature=0).bind_tools(tools)

  class State(TypedDict):
      messages: Annotated[list, add_messages]

  def agent(state: State):
      return {"messages": [llm.invoke(state["messages"])]}

  # 3. 그래프 조립
  builder = StateGraph(State)
  builder.add_node("agent", agent)
  builder.add_node("tools", ToolNode(tools))   # 도구 실행을 대신 해주는 프리빌트 노드

  builder.add_edge(START, "agent")
  # 조건부 엣지: LLM 응답에 도구 호출이 있으면 "tools"로, 없으면 END로
  builder.add_conditional_edges("agent", tools_condition)
  builder.add_edge("tools", "agent")   # 도구 실행 후 다시 agent로 (루프!)

  graph = builder.compile()

  result = graph.invoke({"messages": [{"role": "user", "content": "23 곱하기 17은?"}]})
  print(result["messages"][-1].content)

  - bind_tools → LLM이 "이 도구를 이렇게 불러줘"라는 요청을 반환할 수 있게 됨
  - tools_condition → 그 요청이 있는지 검사해서 자동으로 분기해주는 프리빌트 함수
  - tools → agent 엣지가 루프를 만들어서, 도구 결과를 보고 LLM이 다시 판단합니다

  이 5~6줄이 사실상 "ReAct 에이전트"의 전부입니다. LangGraph엔 이걸 한 줄로 만드는 create_react_agent도 있지만, 위처럼 직접 조립해봐야 내부가
  보여요.

  ---
  3단계: 메모리 (체크포인터)

  지금까지는 invoke가 끝나면 상태가 사라집니다. 대화를 이어가려면 체크포인터를 붙입니다.

  from langgraph.checkpoint.memory import MemorySaver

  memory = MemorySaver()
  graph = builder.compile(checkpointer=memory)   # 2단계 builder 재사용
  memory = MemorySaver()
  graph = builder.compile(checkpointer=memory)   # 2단계 builder 재사용

  config = {"configurable": {"thread_id": "user-1"}}   # 대화 세션 ID

  graph.invoke({"messages": [{"role": "user", "content": "내 이름은 지훈이야"}]}, config)
  r = graph.invoke({"messages": [{"role": "user", "content": "내 이름 뭐랬지?"}]}, config)
  print(r["messages"][-1].content)   # "지훈" 을 기억함

  곱하기 17은?"}]})
  print(result["messages"][-1].content)

  - bind_tools → LLM이 "이 도구를 이렇게 불러줘"라는 요청을 반환할 수 있게
  됨
  - tools_condition → 그 요청이 있는지 검사해서 자동으로 분기해주는
  프리빌트 함수
  - tools → agent 엣지가 루프를 만들어서, 도구 결과를 보고 LLM이 다시
  판단합니다

  이 5~6줄이 사실상 "ReAct 에이전트"의 전부입니다. LangGraph엔 이걸 한 줄로
  만드는 create_react_agent도 있지만, 위처럼 직접 조립해봐야 내부가
  보여요.

  ---
  3단계: 메모리 (체크포인터)

  지금까지는 invoke가 끝나면 상태가 사라집니다. 대화를 이어가려면
  체크포인터를 붙입니다.

  from langgraph.checkpoint.memory import MemorySaver

  memory = MemorySaver()
  graph = builder.compile(checkpointer=memory)   # 2단계 builder 재사용

  config = {"configurable": {"thread_id": "user-1"}}   # 대화 세션 ID
  from langgraph.checkpoint.memory import MemorySaver

  memory = MemorySaver()
  from langgraph.checkpoint.memory import MemorySaver

  from langgraph.checkpoint.memory import MemorySaver

  memory = MemorySaver()

  from langgraph.checkpoint.memory import MemorySaver

  from langgraph.checkpoint.memory import MemorySaver

  from langgraph.checkpoint.memory import MemorySaver

  memory = MemorySaver()

  from langgraph.checkpoint.memory import MemorySaver

  지금까지는 invoke가 끝나면 상태가 사라집니다. 대화를 이어가려면 체크포인터를 붙입니다.

  from langgraph.checkpoint.memory import MemorySaver

  memory = MemorySaver()

  from langgraph.checkpoint.memory import MemorySaver

  memory = MemorySaver()
  graph = builder.compile(checkpointer=memory)   # 2단계 builder 재사용

  config = {"configurable": {"thread_id": "user-1"}}   # 대화 세션 ID

  graph.invoke({"messages": [{"role": "user", "content": "내 이름은 지훈이야"}]}, config)
  r = graph.invoke({"messages": [{"role": "user", "content": "내 이름 뭐랬지?"}]}, config)
  print(r["messages"][-1].content)   # "지훈" 을 기억함

  - thread_id가 같으면 같은 대화로 이어집니다 (여러 사용자 = 여러 thread_id).
  - 실서비스에선 MemorySaver(메모리) 대신 SqliteSaver/PostgresSaver를 씁니다.

  ---
  지금까지 배운 것

  1. State + 리듀서(add_messages)로 데이터 누적
  2. Node에 LLM 호출 넣기
  3. 조건부 엣지 + 루프로 도구 쓰는 에이전트
  4. 체크포인터로 대화 기억

  ---
  다음으로 갈 수 있는 방향입니다:

  - A. 나만의 도구 여러 개 붙여서 실용 에이전트 (웹검색, 계산기, DB 조회 등)
  - B. 멀티 에이전트 — 여러 노드가 서로 다른 역할(리서처/작성자/검토자)로 협업
  - C. RAG 챗봇 — 문서 검색을 그래프에 통합
  - D. Human-in-the-loop — 도구 실행 전에 사람 승인 받기 (interrupt)

  어느 걸 이어서 해볼까요? 아니면 위 3단계 중 막히거나 더 파고들고 싶은 부분이 있으면 말씀해
  주세요. 코드는 지금 바로 복붙해서 돌려보실 수 있습니다.
