FROM mcr.microsoft.com/devcontainers/python:1-3.13-bookworm

# Remove stale Yarn repo source that causes GPG key errors during feature installs
RUN rm -f /etc/apt/sources.list.d/yarn.list

USER vscode
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/home/vscode/.local/bin:${PATH}"
