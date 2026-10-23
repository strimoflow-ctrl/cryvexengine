FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy bots source code and entrypoint
COPY bots/ ./bots/
COPY main.py ./

WORKDIR /app/bots

ENV PORT=5050
ENV PYTHONUNBUFFERED=1

EXPOSE 5050

CMD ["python", "server.py"]
