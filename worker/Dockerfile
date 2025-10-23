FROM python:3-alpine

RUN apk add --no-cache tini=0.19.0-r3

COPY requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt

COPY monitor.py /

RUN adduser -D -u 1000 python
USER python

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python", "/monitor.py"]

