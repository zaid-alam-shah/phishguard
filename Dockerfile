FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data

EXPOSE 8080

ENV FLASK_PORT=8080
ENV FLASK_DEBUG=False
ENV REQUIRE_API_KEY=true
# Set ADMIN_API_KEY environment variable for production use

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "backend.app:app"]
