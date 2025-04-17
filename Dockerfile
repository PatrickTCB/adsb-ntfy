FROM python:3

RUN mkdir app
ADD ./lib app/lib
ADD ./bincraft.py app/
ADD ./main.py app/
ADD ./conf.yml app/

RUN python3 -m pip install geopy
RUN python3 -m pip install zstd
RUN python3 -m pip install requests
RUN python3 -m pip install tzdata
RUN python3 -m pip install pyyaml
RUN python3 -m pip install curlify

WORKDIR /app/

CMD [ "python3", "-u", "main.py" ]