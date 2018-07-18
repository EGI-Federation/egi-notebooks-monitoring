FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7

COPY app /app
RUN pip install -r /app/requirements.txt

ENV JUPYTERHUB_API_URL https://localhost/
ENV JUPYTERHUB_API_TOKEN secret
ENV JUPYTERHUB_API_USER monitoring 
ENV STATUS_FILE /status.json

