FROM python:3.10-slim

WORKDIR /app

# deps système utiles (numpy/scipy wheels, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential \
 && rm -rf /var/lib/apt/lists/*

# copie du framework
COPY . /app

# upgrade pip
RUN pip install --upgrade pip setuptools wheel

# deps python (versions modernes)
RUN pip install "numpy>=1.23,<2.0" "scipy>=1.9,<2.0" "pandas>=1.5,<3.0" \
    "scikit-learn>=1.2,<2.0" "matplotlib>=3.6,<4.0" tqdm

# torch CPU stable
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# rend pipeline exécutable
RUN chmod +x SGmVRNN/pipeline.sh

ENTRYPOINT ["bash", "SGmVRNN/pipeline.sh"]
