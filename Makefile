CURRENT_DIR = $(shell pwd)
USER_NAME = $(shell whoami)
PORT = $(shell expr 1000 + $$RANDOM % 9999)
PHONE ?= 88005553535
API_ID ?= 666
API_HASH ?= 999

build:
	sudo docker build -t bot-container-${USER_NAME}:dev .

run:
	sudo docker run -it --rm \
	    --env-file ${CURRENT_DIR}/.env \
	    -e TG_PHONE=${PHONE} \
	    -e APP_API_ID=${API_ID} \
	    -e APP_API_HASH=${API_HASH} \
	    -p ${PORT}:8888 \
	    -v "${CURRENT_DIR}/src:/srv/tg_bot/src" \
	    -v "${CURRENT_DIR}/data:/srv/data" \
	    --name tg_bot \
	    bot-container-${USER_NAME}:dev

run-debug:
	sudo docker run -it --rm \
	    --env-file ${CURRENT_DIR}/.env \
	    -v "${CURRENT_DIR}/src:/srv/tg_bot/src" \
	    -v "${CURRENT_DIR}/data:/srv/data" \
	    --name tg_bot \
	    bot-container-${USER_NAME}:dev bash

stop:
	sudo docker rm -f tg_bot
