from datetime import datetime
from string import Template
from typing import Optional, List

from django.conf import settings
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.llms import BaseLLM
from langchain.memory import ConversationSummaryBufferMemory, ChatMessageHistory
from langchain.schema import BaseMessage


def construct_memory(llm: BaseLLM, messages: List[BaseMessage] = None) -> ConversationSummaryBufferMemory:
    if messages is not None:
        chat_memory = ChatMessageHistory(messages=messages)
        return ConversationSummaryBufferMemory(
            llm=llm,
            input_key="user_message",
            ai_prefix="Cheerleader",
            human_prefix="Hiring Manager",
            chat_memory=chat_memory
        )
    else:
        return ConversationSummaryBufferMemory(
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
    llm = OpenAI(temperature=0.4)
    memory = construct_memory(llm, messages)
    return LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=settings.DEBUG,
        memory=memory
    )
