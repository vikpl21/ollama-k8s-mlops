FROM python:3.11-slim

RUN pip install --no-cache-dir \
  mlflow==3.11.1 \
  psycopg2-binary==2.9.9 \
  google-cloud-storage==2.16.0

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN useradd -m -u 1000 mlflowuser
USER mlflowuser

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
