FROM python:3.8-slim-buster

ARG PROJECT_NAME=tg_bot
ARG GROUP_ID=5000
ARG USER_ID=5000

ENV PYTHONPATH=/srv/${PROJECT_NAME} \
    # Keeps Python from generating .pyc files in the container
    PYTHONDONTWRITEBYTECODE=1 \
    # Turns off buffering for easier container logging
    PYTHONUNBUFFERED=1

RUN groupadd --gid ${GROUP_ID} ${PROJECT_NAME} && \
    useradd --home-dir /home/${PROJECT_NAME} --create-home --uid ${USER_ID} \
        --gid ${GROUP_ID} --shell /bin/sh --skel /dev/null ${PROJECT_NAME} && \
    mkdir /srv/${PROJECT_NAME} && \
    chown -R ${PROJECT_NAME}:${PROJECT_NAME} /srv/${PROJECT_NAME}

WORKDIR /srv/${PROJECT_NAME}

COPY requirements.txt /srv/${PROJECT_NAME}
COPY src/ /srv/${PROJECT_NAME}/src/

RUN \
    apt-get update && python3.8 -m pip install --upgrade pip && \
    python3.8 -m pip install --no-cache -r requirements.txt

USER ${REMOTE_USER}

CMD ["python3.8", "src/main.py"]