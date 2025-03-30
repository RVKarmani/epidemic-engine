FROM python:3.11.9-alpine3.19

WORKDIR /flask-app

RUN apk update && \
    apk add --no-cache git

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]