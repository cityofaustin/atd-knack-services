FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y build-essential
COPY . /app/atd-knack-services
WORKDIR /app/atd-knack-services
RUN find /app -type f -name "*.py" -exec chmod +x {} \;
RUN pip install -r requirements_production.txt
