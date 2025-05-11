FROM postgres:15-alpine

COPY init.sql /docker-entrypoint-initdb.d/

RUN chmod 755 /docker-entrypoint-initdb.d/init.sql