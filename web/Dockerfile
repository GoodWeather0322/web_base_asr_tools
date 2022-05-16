FROM python:3.8
ADD ./code/requirements.txt /web/code/requirements.txt
WORKDIR /web/code
RUN apt-get update -y && apt-get install -y --no-install-recommends build-essential gcc libsndfile1 
RUN apt-get install libpython2.7
RUN pip install -r requirements.txt