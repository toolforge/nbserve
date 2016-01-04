FROM debian:jessie

MAINTAINER Yuvi Panda <yuvipanda@riseup.net>
RUN echo shit
RUN apt-get update
RUN apt-get install --yes --no-install-recommends \
    python3.4 \
    python3-pip \
    python3.4-dev

COPY . /srv/nbserve/

RUN pip3 install ipython tornado nbconvert

EXPOSE 8889
