FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y curl python3 python3-pip sudo && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    useradd -ms /bin/bash ollama

USER ollama
WORKDIR /home/ollama

COPY --chown=ollama:ollama requirements.txt ./
RUN pip install --user -r requirements.txt

COPY --chown=ollama:ollama app ./app
COPY --chown=ollama:ollama start.sh ./start.sh
RUN chmod +x start.sh

EXPOSE 8080 11434

ENTRYPOINT ["./start.sh"]
