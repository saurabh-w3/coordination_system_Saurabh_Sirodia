import os, json
USE_LLM = True
try:
    from langgraph.graph import StateGraph, START, END
    from langchain_openai import ChatOpenAI
except Exception:
    USE_LLM = False

def create_llm(model_env_var='OPENAI_MODEL', key_env_var='OPENAI_API_KEY'):
    model_name = os.getenv(model_env_var, 'gpt-4o-mini')
    api_key = os.getenv(key_env_var, '')
    if USE_LLM and api_key:
        return ChatOpenAI(model=model_name, temperature=0.2, api_key=api_key)
    return None  # caller should fallback to heuristic

def run_single_decision_graph(llm, system_prompt: str, user_payload: dict):
    """If LLM is available, run a tiny LangGraph with one decision node; else return None."""
    if llm is None:
        return None
    from pydantic import BaseModel
    class State(BaseModel):
        context: dict
        plan: dict = {}
    def decide(state: State) -> State:
        messages = [
            {"role":"system","content": system_prompt},
            {"role":"user","content": json.dumps(user_payload, ensure_ascii=False)}
        ]
        response = llm.invoke(messages)
        try:
            state.plan = json.loads(response.content)
        except Exception:
            state.plan = {}
        return state
    graph = StateGraph(State)
    graph.add_node('decide', decide)
    graph.add_edge(START, 'decide')
    graph.add_edge('decide', END)
    app = graph.compile()
    try:
        out = app.invoke({'context': user_payload})
        data = out.get('plan', {})
        # minimal schema check
        if not isinstance(data, dict) or 'intents' not in data:
            return {}
        if not isinstance(data['intents'], list):
            return {}
        return data
    except Exception:
        return {}
