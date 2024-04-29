# Base image for build stage
# AWS Lambda Python runtime as the base image
FROM 3.10-alpine as build

RUN yum -y install amazon-linux-extras
RUN yum -y install Xvfb
RUN yum -y install wget
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.32.2/geckodriver-v0.32.2-linux64.tar.gz
RUN yum -y install tar 
RUN tar -xf geckodriver-v0.32.2-linux64.tar.gz
RUN mv geckodriver /usr/local/bin/
RUN export MOZ_HEADLESS=1
RUN export HOME=/tmp/profile

ENV HOME="/tmp"
ENV SE_CACHE_PATH="/tmp/firefox"