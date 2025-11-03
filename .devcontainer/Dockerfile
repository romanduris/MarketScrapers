# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12

# Voliteľné: inštalácia základných nástrojov
RUN apt-get update && apt-get install -y git curl && apt-get clean -y

# Nastavenie pracovného adresára
WORKDIR /workspace

# Zabezpečí, že pip je dostupný
RUN python3 -m ensurepip
