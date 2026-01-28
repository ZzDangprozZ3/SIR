FROM python:3.10-slim

WORKDIR /app

# Installer les dependances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les scripts
COPY convert.py .
COPY utils.py .
COPY AOC_IDS_FINI.py .
COPY validation.py .

# Volumes pour les donnees
# /data/input  -> Dataset NetMob23
# /data/output -> CSV generes
VOLUME ["/data/input", "/data/output"]

CMD ["echo", "Utiliser: python convert.py ou python AOC_IDS_FINI.py"]
