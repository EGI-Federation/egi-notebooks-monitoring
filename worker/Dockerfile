FROM python:3-alpine

RUN apk add --no-cache tini=0.19.0-r3

COPY requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

COPY monitor.py /

ENV JUPYTERHUB_API_URL https://localhost/
ENV JUPYTERHUB_API_TOKEN secret
ENV JUPYTERHUB_API_USER monitoring
ENV STATUS_FILE /status.json

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python", "/monitor.py"]

