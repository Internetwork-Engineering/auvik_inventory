FROM python:3.8-buster
COPY . /src
WORKDIR /src
RUN python setup.py install
CMD ["go_autoie"]
