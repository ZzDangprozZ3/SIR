
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    tqdm \
    networkx \
    scikit-learn \
    requests \
    argparse \
    configparser

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN mkdir -p /app/data_collected

COPY . /app

RUN chmod +x /app/pipeline.sh

CMD ["bash", "pipeline.sh"]