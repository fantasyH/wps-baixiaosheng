FROM python:3.12-slim AS backend
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py skill_engine.py llm_synthesis.py ./
COPY data/ ./data/
COPY .env ./
COPY .ach_token.json ./

FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npx vite build

FROM python:3.12-slim
WORKDIR /app
COPY --from=backend /app ./
COPY --from=frontend /build/dist ./frontend/dist/

EXPOSE 5099
CMD ["python", "app.py"]
