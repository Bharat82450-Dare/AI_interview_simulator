#!/bin/bash
set -e

# Install spacy model
pipenv run python -m spacy download en_core_web_md

# Pre-download SentenceTransformers model to cache
pipenv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
