FROM python:3.9

WORKDIR /file-converter-api
RUN apt-get update
RUN apt-get install -y ffmpeg
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 80

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000" ]