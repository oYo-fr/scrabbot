# syntax=docker/dockerfile:1

FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

ENV PATH=/usr/local/bin:${PATH} \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    unzip \
    zip \
    bash \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    locales \
    sudo \
    python3 \
    python3-pip \
    python3-venv \
    libgl1 \
    libglu1-mesa \
    libx11-6 \
    libxext6 \
    libxi6 \
    libxrender1 \
    libxrandr2 \
    libxxf86vm1 \
    libfontconfig1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf python3 /usr/bin/python

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g npm@latest

# Install GitHub CLI from official repository
RUN if ! command -v gh >/dev/null 2>&1; then \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg; \
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends gh; \
    rm -rf /var/lib/apt/lists/*; \
    fi

# Create vscode user properly for devcontainer
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid vscode --shell /bin/bash --create-home vscode \
    && echo 'vscode ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode \
    && chown -R vscode:vscode /home/vscode \
    && chmod 755 /home/vscode

USER vscode

# Configure Git to avoid pager blocking in terminal and set identity
RUN git config --global core.pager cat \
    && git config --global init.defaultBranch main \
    && git config --global user.email "dev@scrabbot.local" \
    && git config --global user.name "Scrabbot Dev" \
    && git config --global --add safe.directory /workspaces/Scrabbot

# Add Rust to PATH for the current session
ENV PATH="/home/vscode/.cargo/bin:${PATH}"

# Reset entrypoint to default
ENTRYPOINT []
CMD ["sleep", "infinity"]
