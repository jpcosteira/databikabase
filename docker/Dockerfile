FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME=0.0.0.0


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 jpc && \
    useradd -m -u 1000 -g jpc jpc
 
 
# Set the workdir
WORKDIR /home/jpc

COPY docker/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

#COPY app/* .

EXPOSE 7860 8888
# Switch to the custom user
USER jpc

CMD ["sh", "-c", "python app.py"]

