# Frontend and API on one auth-protected origin (educational demo only).
FROM node:22-alpine AS ui
WORKDIR /web
COPY testir/package*.json ./
RUN npm ci
COPY testir/src ./src
COPY testir/public ./public
ENV REACT_APP_API_BASE_URL=
RUN npm run build
FROM python:3.12-slim
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=preview
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY uk.csv ./uk.csv
COPY v2/__init__.py ./v2/__init__.py
COPY v2/api ./v2/api
COPY --from=ui /web/build ./v2/static
CMD ["sh", "-c", "exec uvicorn v2.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
