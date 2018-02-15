FROM python:3.6

WORKDIR /usr/src/app

ADD . /usr/src/app

COPY requirements.txt ./

# RUN apt-get install libffi-dev python3.6-dev

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD [ "python", "./main.py", "-p", "/data" ]
