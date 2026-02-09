FROM python:3.11-slim
WORKDIR /app
COPY services/alert_receiver/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY services/alert_receiver/. /app
CMD ["python", "app.py"]
