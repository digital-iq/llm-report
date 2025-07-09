FROM ubuntu:22.04

# Install dependencies and Ollama
RUN apt-get update && \
    apt-get install -y curl sudo && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    useradd -ms /bin/bash ollama

USER ollama
WORKDIR /home/ollama

# Create prompt dir for mounting
RUN mkdir -p /home/ollama/prompts

# Copy the startup script
COPY --chown=ollama:ollama start.sh /home/ollama/start.sh
RUN chmod +x /home/ollama/start.sh

RUN chmod -R 777 /home/ollama/.ollama

# Expose the Ollama API port
EXPOSE 11434

# Set ENV for model
ARG MODEL_NAME
ENV MODEL_NAME=${MODEL_NAME}

# Start via our script
ENTRYPOINT ["/home/ollama/start.sh"]
