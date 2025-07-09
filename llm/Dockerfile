# Stage 1: Build the Ollama runtime
FROM ubuntu:22.04

# Install Ollama and dependencies
RUN apt-get update && \
    apt-get install -y curl sudo && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    useradd -ms /bin/bash ollama

USER ollama
WORKDIR /home/ollama

# Inject model name via build-time argument or ENV
ARG MODEL_NAME
ENV MODEL_NAME=${MODEL_NAME}

# Pull the model at build time
RUN ollama pull $MODEL_NAME

# Create a directory for prompt mounting
RUN mkdir -p /home/ollama/prompts

# Expose Ollama API
EXPOSE 11434

# Serve with prompt file as system prompt
CMD ollama serve --model $MODEL_NAME
