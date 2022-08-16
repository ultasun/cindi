# Welcome to the cindi, which is intended to be used as part of a larger
# docker-compose outfit.
#
# WARNING: If you only want to play with the INDI language, or if you're using
# a laptop/mobile on battery power, or if you're not interested in consuming
# a lot of RAM/resources; then please use the 'cindi-lite' image instead!
#
# WARNING: Trying to use this image without the docker-compose.yml provided by
# the author could be labor intensive, please use `docker compose`! Check the
# README! Thank you for reading!
#

# --- VOLUMES ---------
# There are 3 volumes that a user (you) might be concerned with:
# /app/data   :: the SQLite3 database will be stored in this directory
# /app/logs   :: a file for each DDL or DML statement 
# /app/config :: the two configuration files (stores.txt and tables.txt)
#
# It is not 'necessary' to bind-mount or name-mount any of these directories,
# unless you wish to persist data, or manipulate CINDI from the outside.

# --- TCP PORTS  ------
# CINDI's default listen port for the Flask HTTP Development server is 36963.  

# --- HOW TO USE ------
# 1) $ docker build -t cindi .
# 2) $ docker run -dp 36963:36963 -v cindi-sqlite3-data:/app/data -v cindi-logs:/app/logs cindi 
# 2a) adding a bind-mount for /app/config is an option, if you have the .txt's!
# 3) `docker exec -it` into the container, and populate with 'EXAMPLE' data:
# 3a) `$ python`
# 3b) `>>> import cindi`
# 3c) `>>> cindi.quick_unit_tests()`
# 3d) Verify the last line printed is 'True' which means all 17 tests passed!

# ----------------------
# Beginning of the 'cindi' Dockerfile

# Use Official Python from Official Debian Bullseye
FROM python:bullseye

# Update / Upgrade the Debian system
RUN apt-get update ; apt-get -y upgrade

# Install CINDI's dependency dependencies (just postgresql library support)
RUN apt-get -y install libpq5

# Upgrade pip
RUN pip install --upgrade pip

# most packages are not available in the test.pypi.org index.
# uncomment the next line if installing cindi from test.pypi.org
#RUN pip install psycopg ; pip install psycopg[pool] ; pip install redis ; pip install mysql-connector-python ; pip install flask ; pip install flask_cors; pip install pyOpenSSL ; pip install pymongo

# Install the full CINDI pip package (with all optional dependencies)
RUN pip install cindi[mysql,postgres,mongodb,redis]

# Create a non-privileged user for the runtime, home directory /app
RUN useradd -m -d /app -s /bin/sh -u 36963 python-user

# Switch the starting directory to /app
WORKDIR /app

# Install the files into the image
COPY LICENSE .
COPY README.md .
COPY Dockerfile .
COPY docker-compose.yml .
COPY app.py .
COPY bootloader.sh .
COPY init-nonsense-sqlite3.sql .
COPY init-nonsense-mysql.sql .
COPY init-nonsense-postgresql.sql .
COPY init-nonsense-mongodb.js .
COPY sqlite3_initialization_helper.py .
COPY config/stores.txt config/stores.txt
COPY config/tables.txt config/tables.txt

# set permissions on named volume targets
RUN mkdir -p /app/data && chown -R python-user /app/data
RUN mkdir -p /app/logs && chown -R python-user /app/logs

# Switch user away from root privilege
USER 36963

# Start CINDI
CMD [ "./bootloader.sh" ]

# ----------------------
# End of the 'cindi' Dockerfile
