from datetime import datetime
from string import Template
from typing import Optional, List

from django.conf import settings
from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM, PromptLayerOpenAIChat
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.schema import BaseMessage


def construct_memory(llm: BaseLLM, messages: List[BaseMessage] = None) -> ConversationBufferMemory:
    if messages is not None:
        chat_memory = ChatMessageHistory(messages=messages)
        return ConversationBufferMemory(
            llm=llm,
            input_key="user_message",
            ai_prefix="Cheerleader",
            human_prefix="Hiring Manager",
            chat_memory=chat_memory
        )
    else:
        return ConversationBufferMemory(
            llm=llm,
            input_key="user_message",
            ai_prefix="Cheerleader",
            human_prefix="Hiring Manager"
        )


def generate_bot(messages: Optional[List[BaseMessage]] = None) -> LLMChain:
    with open(settings.PROMPT_FILE_PATH, "r") as prompt_file:
        template = Template(prompt_file.read())

    template_string = template.substitute(
        current_date=datetime.now().strftime('%B %Y')
    ).strip()
    prompt = PromptTemplate(
        input_variables=[
            "history",
            "user_message",
        ],
        template=template_string
    )
    llm = PromptLayerOpenAIChat(
        model_name=settings.OPENAI_MODEL_NAME,
        temperature=0.4
    )
    memory = construct_memory(llm, messages)
    return LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=settings.DEBUG,
        memory=memory
    )
