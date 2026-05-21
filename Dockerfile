# Stage 1: build React frontend
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python API + static files
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py data_manager.py utils.py dependencies.py schemas.py exceptions.py start.sh ./
COPY routers ./routers/
COPY services ./services/
COPY data/ ./data/
COPY --from=frontend /app/static/dist ./static/dist

# Windows checkouts often use CRLF; fix shebang so ./start.sh runs in Linux
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
