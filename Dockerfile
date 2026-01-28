FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    numpy==1.23.1 pandas==1.3.5 scikit-learn==1.0.2 scipy==1.8.0 \
    pyarrow==9.0.0 fastparquet==0.8.1 torch==1.12.1 torchvision==0.13.1 \
    datasets==1.18.3 transformers==4.21.1 tokenizers==0.12.1 \
    pyod==1.0.9 seaborn==0.11.2 jupyter matplotlib tqdm \
    absl-py protobuf tensorboard google-auth google-auth-oauthlib \
    grpcio markdown werkzeug

CMD ["bash"]
