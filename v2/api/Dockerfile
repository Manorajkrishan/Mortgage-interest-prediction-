FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY uk.csv ./uk.csv
COPY v2/api ./v2/api
COPY v2/__init__.py ./v2/__init__.py
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
CMD ["sh", "-c", "exec uvicorn v2.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
