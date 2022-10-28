FROM docker-registry.wikimedia.org/bullseye

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update -y \
    && apt-get upgrade -y \
    && apt-get -y install slapd ldap-utils

COPY schemas/*.schema /etc/ldap/schema
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 389/tcp

ENTRYPOINT [ "/entrypoint.sh"]
