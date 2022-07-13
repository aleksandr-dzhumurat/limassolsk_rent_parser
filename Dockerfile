FROM python:3.10

ENV PYTHONPATH=/srv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/

COPY requirements.txt /srv/
RUN python3.10 -m pip install --upgrade pip

RUN \
    python3.10 -m pip install --no-cache -r requirements.txt

COPY src/ /srv/src/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
