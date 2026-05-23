# 자가 호스팅용 앱 이미지 (앱 + LibreOffice 미리보기 + 한글폰트)
FROM python:3.12-slim

# LibreOffice(미리보기 변환) + 한글 폰트
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-impress \
        fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true", "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
