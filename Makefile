CURRENT_DIR = $(shell pwd)
USER_NAME = $(shell whoami)
PORT = $(shell expr 1000 + $$RANDOM % 9999)
include .env
export

build:
	docker build \
		-t bot-container-${USER_NAME}:dev .

train:
	docker run -it --rm \
	    --env-file ${CURRENT_DIR}/.env \
	    -v "${CURRENT_DIR}/src:/srv/src" \
	    -v "${CURRENT_DIR}/data:/srv/data" \
	    --name tg_bot \
	    bot-container-${USER_NAME}:dev train

run:
	docker run -it --rm \
	    --env-file ${CURRENT_DIR}/.env \
	    -p ${PORT}:8888 \
		-e DEBUG=${DEBUG} \
	    -v "${CURRENT_DIR}/src:/srv/src" \
	    -v "${CURRENT_DIR}/data:/srv/data" \
	    --name tg_bot \
	    bot-container-${USER_NAME}:dev serve

score:
	docker run -it --rm \
	    --env-file ${CURRENT_DIR}/.env \
	    -p ${PORT}:8888 \
		-e MODE=${MODE} \
	    -v "${CURRENT_DIR}/src:/srv/src" \
	    -v "${CURRENT_DIR}/data:/srv/data" \
	    --name tg_bot \
	    bot-container-${USER_NAME}:dev score

run-debug:
	docker run -it --rm \
	    --env-file ${CURRENT_DIR}/.env \
	    -v "${CURRENT_DIR}/src:/srv/tg_bot/src" \
	    -v "${CURRENT_DIR}/data:/srv/data" \
	    --name tg_bot \
	    bot-container-${USER_NAME}:dev bash

stop:
	docker rm -f tg_bot
