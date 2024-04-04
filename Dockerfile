FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y build-essential
COPY . /app/atd-knack-services
WORKDIR /app
RUN find /app -type f -name "*.py" -exec chmod +x {} \;
RUN pip install -r /app/atd-knack-services/requirements_production.txt
