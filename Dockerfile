FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HEALTH_HOST=0.0.0.0
ENV HEALTH_PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vip_payment_bot ./vip_payment_bot
COPY scripts ./scripts

EXPOSE 8080

CMD ["python", "-m", "vip_payment_bot"]
