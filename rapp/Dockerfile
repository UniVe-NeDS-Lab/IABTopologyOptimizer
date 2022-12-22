FROM nginx/unit:1.28.0-python3.10

RUN mkdir build

COPY requirements.txt /build/requirements.txt

RUN apt update && apt install -y python3-pip                                  \
    && pip3 install --no-cache-dir -r /build/requirements.txt -r /build/iab_manager/requirements.txt \
    && apt remove -y python3-pip                                              \
    && apt autoremove --purge -y                                              \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list

# OK, that looks strange but here's a explanation from Nginx docs
# https://unit.nginx.org/howto/docker/:

# """ PIP isn't installed by default, so we install it first.
# Next, we install the requirements, remove PIP, and perform image cleanup. """

# Note we use /build/requirements.txt since this is our file

COPY ./config.json /docker-entrypoint.d/config.json

COPY . /build/

EXPOSE 80