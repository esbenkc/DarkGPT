ARG PYTHON_VERSION=3.12.3

FROM python:${PYTHON_VERSION}-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        bash-completion \
        git-lfs \
        groff \
        jq \
        less \
        nano \
        rsync \
 && rm -rf /var/lib/apt/lists/* \
 && git lfs install

RUN pip install --no-cache-dir \
        poetry==1.8.3

WORKDIR /source
COPY pyproject.toml poetry.lock ./
RUN POETRY_VIRTUALENVS_CREATE=false \
    poetry install \
    --no-cache \
    --no-root \
    --with dev

ARG APP_USER=darkgpt
ARG APP_DIR=/home/${APP_USER}/app
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} ${APP_USER} \
 && useradd -m -u ${USER_ID} -g ${APP_USER} -s /bin/bash ${APP_USER} \
 && mkdir -p ${APP_DIR} /home/${APP_USER}/.aws \
 && chown -R ${USER_ID}:${GROUP_ID} ${APP_DIR} /home/${APP_USER}

WORKDIR ${APP_DIR}
COPY . .
RUN POETRY_VIRTUALENVS_CREATE=false \
    poetry install
USER ${APP_USER}
