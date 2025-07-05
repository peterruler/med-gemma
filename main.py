# main.py
import chainlit as cl
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser, HumanMessage
from langchain.schema.runnable.config import RunnableConfig
import base64
import os
from typing import List, Dict, Any
import requests
import json


async def process_image_with_ollama(model_name: str, image_base64: str, prompt: str) -> str:
    """Process an image with Ollama using the vision model via a direct API call."""
    ollama_url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    try:
        # Use a synchronous request in a thread to avoid blocking the event loop
        loop = cl.context.loop
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(ollama_url, json=payload, timeout=60)
        )
        response.raise_for_status()
        return response.json().get("response", "Error processing image.")
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Ollama: {str(e)}"


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session with Med Gemma."""
    elements = [
        cl.Image(name="medgemma-logo", display="inline", path="medgemma.jpeg"),
    ]
    await cl.Message(
        content="👩‍⚕️ Hello, I'm **Med Gemma**. Ask me anything medical! You can also upload medical images for analysis.",
        elements=elements,
    ).send()

    # Use the Ollama model with vision support
    model = Ollama(model="edwardlo12/medgemma-4b-it-Q4_K_M")
    cl.user_session.set("model", model)

    # Create a runnable for text-only messages
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are Med Gemma, a certified virtual physician. "
                    "Respond **only** with medical information that is factual, "
                    "concise, and evidence-based. If unsure, say you don't know. "
                    "When analyzing medical images, provide detailed observations "
                    "and potential diagnoses while emphasizing the need for professional consultation."
                ),
            ),
            ("human", "{question}"),
        ]
    )

    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages with text and/or images."""
    model = cl.user_session.get("model")  # Get the Ollama model instance
    runnable = cl.user_session.get("runnable")

    # Check if the message contains images
    if message.elements:
        image_element = next((el for el in message.elements if isinstance(el, cl.Image)), None)
        if image_element:
            with open(image_element.path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

            prompt_text = f"""
Analyze this medical image in detail. User's question: {message.content}
"""
            
            msg = cl.Message(content="Analyzing the image, please wait...")
            await msg.send()

            # Call the robust function to handle the image
            response_text = await process_image_with_ollama(
                "edwardlo12/medgemma-4b-it-Q4_K_M",
                image_base64,
                prompt_text
            )

            msg.content = response_text
            await msg.update()
            return

    # Handle text-only messages (no changes here)
    reply = cl.Message(content="")
    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await reply.stream_token(chunk)

    await reply.send()
