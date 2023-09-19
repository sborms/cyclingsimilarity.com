FROM python:3.9

WORKDIR /api

COPY . /api

RUN mkdir -p /src

COPY ../src /api/src

RUN pip install -r requirements.txt

ENTRYPOINT [ "uvicorn" ]

EXPOSE 8080

CMD [ "--host", "0.0.0.0", "--port", "8080", "main:app"]