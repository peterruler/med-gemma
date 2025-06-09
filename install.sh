#!/bin/bash
ollama pull alibayram/medgemma:latest
conda activate torch31111
pip install chainlit langchain-community ollama