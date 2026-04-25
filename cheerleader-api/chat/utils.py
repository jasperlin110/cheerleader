from datetime import datetime
from string import Template
from typing import Iterator, List

from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph


def _create_app():
    with open(settings.PROMPT_FILE_PATH, "r") as prompt_file:
        template = Template(prompt_file.read())

    system_prompt = template.substitute(
        current_date=datetime.now().strftime('%B %Y')
    ).strip()

    workflow = StateGraph(state_schema=MessagesState)
    model = ChatAnthropic(model=settings.MODEL_NAME, temperature=0.4)

    def call_model(state: MessagesState):
        messages = state["messages"]
        if not any(msg.type == "system" for msg in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
        return {"messages": model.invoke(messages)}

    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)
    return workflow.compile(checkpointer=MemorySaver())


def stream_response(
    prior_messages: List[BaseMessage], user_message: str, thread_id: str
) -> Iterator[str]:
    app = _create_app()
    config = {"configurable": {"thread_id": thread_id}}
    for chunk, _ in app.stream(
        {"messages": prior_messages + [HumanMessage(content=user_message)]},
        config=config,
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            yield str(chunk.content)
