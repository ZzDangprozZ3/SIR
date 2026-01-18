FROM python:3.6-slim

ENV PYTHONUNBUFFERED=1

# system deps for building/installing packages and for TensorFlow 1.5
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential git wget ca-certificates libssl-dev libffi-dev \
      libatlas-base-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy and install python requirements (including git+ packages)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# copy project
# COPY . /app

# make run script executable
RUN [ -f /app/run.sh ] && chmod +x /app/run.sh || true

# output dir
RUN mkdir -p /app/webankdata

VOLUME ["/app/webankdata", "/app/train_ticket"]

# CMD ["python", "-m", "traceanomaly.main","--trainpath", "./train_ticket/train/train","--normalpath", "./train_ticket/test_normal/test_normal","--abnormalpath", "./train_ticket/test_abnormal/test_abnormal","--outputpath", "result","-c", "flow_type=rnvp"]
CMD ["python", "-m", "traceanomaly.main","--trainpath", "./merged_flows","--normalpath", "./merged_flows","--abnormalpath", "./merged_flows","--outputpath", "result","-c", "flow_type=rnvp"]