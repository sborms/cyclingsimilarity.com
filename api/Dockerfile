FROM python:3.9

WORKDIR /api

COPY api/. /api

COPY src/. /api/src

# COPY .env /api

# RUN pip install --upgrade pip
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.0.1+cpu
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "uvicorn" ]

EXPOSE 8000

CMD [ "--host", "0.0.0.0", "--port", "8000", "main:app" ]