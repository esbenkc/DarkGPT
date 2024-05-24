ARG PYTHON_VERSION=3.12.3
ARG AWS_CLI_VERSION=2.15.49

FROM amazon/aws-cli:${AWS_CLI_VERSION} AS aws-cli

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

COPY --from=aws-cli /usr/local/aws-cli/v2/current /usr/local

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

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
USER ${APP_USER}
