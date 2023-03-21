FROM python:3.11

RUN pip install motor pytest pytest-asyncio

ADD . /app
