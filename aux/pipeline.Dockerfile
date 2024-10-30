FROM public.ecr.aws/docker/library/python:3.10.13-bookworm

RUN apt-get update && apt-get install -y \
    zip \ 
    git

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"  
