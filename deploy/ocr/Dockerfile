# Tesseract OCR (Apache-2.0) + Polish model, for hosts without a system binary: docker build -t riskminer-ocr deploy/ocr
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-pol && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["tesseract"]
