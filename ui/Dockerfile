FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine

COPY app /app
RUN pip install --no-cache-dir -r /app/requirements.txt

ENV JUPYTERHUB_API_URL https://localhost/
ENV JUPYTERHUB_API_TOKEN secret
ENV JUPYTERHUB_API_USER monitoring 
ENV STATUS_FILE /status.json

