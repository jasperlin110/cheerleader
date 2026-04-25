from datetime import datetime
from string import Template
from typing import List, Optional

from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph


def create_langgraph_app(messages: Optional[List[BaseMessage]] = None):
    with open(settings.PROMPT_FILE_PATH, "r") as prompt_file:
        template = Template(prompt_file.read())

    system_prompt = template.substitute(
        current_date=datetime.now().strftime('%B %Y')
    ).strip()

    workflow = StateGraph(state_schema=MessagesState)

    model = ChatAnthropic(
        model=settings.MODEL_NAME,
        temperature=0.4,
    )

    def call_model(state: MessagesState):
        messages = state["messages"]
        if not messages or not any(msg.type == "system" for msg in messages):
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=system_prompt)] + messages
        response = model.invoke(messages)
        return {"messages": response}

    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def generate_bot(messages: Optional[List[BaseMessage]] = None):
    return create_langgraph_app(messages)
