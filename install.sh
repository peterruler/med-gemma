#!/bin/bash
ollama pull edwardlo12/medgemma-4b-it-Q4_K_M
conda activate torch31111
pip install chainlit langchain-community ollama