FROM python:3.8-slim
WORKDIR /app
RUN apt-get update -y && apt-get install tesseract-ocr tesseract-ocr-ind -y
# RUN pip3 install --upgrade pip
# RUN pip3 install opencv-python-headless google-cloud-vision waitress sanic matplotlib
RUN pip3 install opencv-python-headless cycler kiwisolver matplotlib numpy sanic Pillow pyparsing pytesseract python-dateutil six
COPY . /app
ENTRYPOINT ["python3"]
#CMD ["main.py"]