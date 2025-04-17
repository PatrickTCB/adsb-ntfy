FROM python:3

RUN mkdir app
ADD ./lib app/lib
ADD ./bincraft.py app/
ADD ./main.py app/

RUN python3 -m pip install geopy
RUN python3 -m pip install zstd
RUN python3 -m pip install requests
RUN python3 -m pip install tzdata

WORKDIR /app/

CMD [ "python3", "-u", "main.py" ]