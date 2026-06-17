FROM mcr.microsoft.com/devcontainers/jekyll:2-bullseye

COPY post-start.sh /usr/local/bin/devcontainer-post-start

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --no-cache-dir pre-commit \
    && chmod 755 /usr/local/bin/devcontainer-post-start
