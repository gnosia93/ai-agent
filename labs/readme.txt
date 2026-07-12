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
