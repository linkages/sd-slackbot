#!/bin/bash

distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
    && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
	sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
	sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y docker-compose nvidia-docker2 virtualenvwrapper emacs-nox

mkdir /export
mkdir -p /export/slackbot/outputs

#docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
