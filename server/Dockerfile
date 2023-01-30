FROM python:3

RUN pip install poetry

ADD server.py /
ADD data.txt /
ADD pyproject.toml /
ADD poetry.lock /

RUN poetry install
