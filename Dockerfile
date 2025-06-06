FROM docker-registry.wikimedia.org/python3-bookworm:latest

RUN apt-get update && apt-get install -y git \
python3-bitu-ldap \
python3-bs4 \
python3-django \
python3-django-auth-ldap \
python3-django-captcha \
python3-djangorestframework \
python3-django-rq \
python3-ldap3 \
python3-mysqldb \
python3-mwclient \
python3-pyotp \
python3-paramiko \
python3-passlib \
python3-qrcode \
python3-sshpubkeys \
python3-social-django \
python3-structlog \
uwsgi-plugin-python3

COPY src/ /usr/lib/python3/dist-packages/
COPY scripts/bitu /usr/bin/bitu
COPY scripts/entry_point.sh /usr/bin/entry_point.sh
COPY src/bitu/bitu/docker_settings.py /etc/bitu/settings.py
#COPY requirements-docker.txt /
#RUN pip3 install -r requirements-docker.txt

ENTRYPOINT ["/usr/bin/entry_point.sh"]