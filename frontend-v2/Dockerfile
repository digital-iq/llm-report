FROM python:3.10-slim

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Copy React build output
COPY build ./app/static

EXPOSE 8080

CMD ["python", "app/app.py"]

