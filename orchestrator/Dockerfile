FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y ruby-full

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN gem install asciidoctor-pdf
# Copy the entire app folder
COPY app ./app

EXPOSE 8080

CMD ["python", "./app/app.py"]
