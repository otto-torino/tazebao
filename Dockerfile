# Local development and test image (production runs in a virtualenv on the server).
# See docker-compose.yml and the "Docker" section of the README.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# mysqlclient is built from source: compiler, pkg-config and the client headers
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY tazebao/requirements/ /tmp/requirements/
RUN pip install -r /tmp/requirements/local.txt

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

# the code is mounted at /app by docker-compose
WORKDIR /app/tazebao
ENTRYPOINT ["entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
