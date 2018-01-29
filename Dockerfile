FROM python:2.7

EXPOSE 8888

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip install -r requirements.txt

COPY . /usr/src/app

CMD ["/bin/bash"]
