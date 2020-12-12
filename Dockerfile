FROM python:3.8-slim

# Copy our own application
WORKDIR /app
COPY . /app/atd-knack-services

RUN chmod -R 755 /app/*

# # Proceed to install the requirements...do
RUN cd /app/atd-knack-services && apt-get update && \
    pip install -r requirements_production.txt