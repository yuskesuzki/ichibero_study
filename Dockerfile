FROM python:3.10-slim-bullseye as base

RUN apt update
RUN apt install -y libexpat1
RUN pip3 install --no-cache-dir fastapi uvicorn[standard] rio-tiler
