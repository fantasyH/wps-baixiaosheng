FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
COPY data/ ./data/
COPY index.html .
EXPOSE 5099
CMD ["python", "server.py", "--port", "5099", "--host", "0.0.0.0"]
