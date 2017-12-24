FROM ubuntu:17.04

MAINTAINER Hugo Sousa
ENV DJANGO_PROJECT=buy_a_ticket
ENV DOCKYARD_SRVHOME=/opt
ENV DOCKYARD_SRVPROJ=$DOCKYARD_SRVHOME/$DJANGO_PROJECT

RUN useradd --create-home ubuntu && \
    apt-get update && \
    apt-get -y install \
                   git \
                   locales \
                   libmysqlclient-dev \
                   libssl-dev \
                   wget \
                   build-essential \
                   nginx \
                   python-pip \
                   mongodb-server

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV PYENV_ROOT /home/ubuntu/.pyenv
ENV PYTHON_VERSION 3.6.2
ENV PATH $PYENV_ROOT/versions/$PYTHON_VERSION/bin/:$PYENV_ROOT/shims:$PYENV_ROOT/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN git clone https://github.com/yyuu/pyenv.git $PYENV_ROOT && \
    eval "$(pyenv init -)" && \
    pyenv install $PYTHON_VERSION && \
    ln -s $PYENV_ROOT/versions/$PYTHON_VERSION/bin/python /usr/bin/python3


WORKDIR $DOCKYARD_SRVPROJ
ADD . $DOCKYARD_SRVPROJ
RUN mkdir logs
VOLUME ["$DOCKYARD_SRVHOME/logs/"]

RUN pip install -r $DOCKYARD_SRVPROJ/requirements.txt

EXPOSE 8000

RUN mkdir -p /data/db
RUN service mongodb start

ADD docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
