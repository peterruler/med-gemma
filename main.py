# main.py
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable.config import RunnableConfig
import chainlit as cl


@cl.on_chat_start
async def on_chat_start():
    # Show a little avatar or logo (optional)
    elements = [
        cl.Image(name="medgemma-logo", display="inline", path="medgemma.jpeg"),
    ]
    await cl.Message(
        content="👩‍⚕️ Hello, I’m **Med Gemma**. Ask me anything medical!",
        elements=elements,
    ).send()

    #      ──> make sure the model is available locally:
    #      $ ollama pull alibayram/medgemma:latest
    model = Ollama(model="alibayram/medgemma:latest")  # update tag if needed

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are Med Gemma, a certified virtual physician. "
                    "Respond **only** with medical information that is factual, "
                    "concise, and evidence-based. If unsure, say you don't know."
                ),
            ),
            ("human", "{question}"),
        ]
    )

    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")

    reply = cl.Message(content="")
    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await reply.stream_token(chunk)

    await reply.send()
