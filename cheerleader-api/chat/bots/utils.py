from datetime import datetime
from string import Template

from django.conf import settings
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory


def generate_bot() -> LLMChain:
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
    memory = ConversationSummaryBufferMemory(
        llm=llm,
        input_key="user_message",
        ai_prefix="Cheerleader",
        human_prefix="Hiring manager"
    )
    return LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True,
        memory=memory
    )
