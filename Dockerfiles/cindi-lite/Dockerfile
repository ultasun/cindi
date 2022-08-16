# Welcome to the cindi-lite demo, which by default, only utilizes SQLite3.
#
# WARNING: If you want to use anything other than SQLite3, please consider
# using the 'cindi' image instead. This 'cindi-lite' edition is only suitable
# for SQLite3. Check the README! Thank you for reading!

# --- VOLUMES ---------
# There are 3 volumes that a user (you) might be concerned with:
# /app/data   :: the SQLite3 database will be stored in this directory
# /app/logs   :: a file for each DDL or DML statement 
# /app/config :: the two configuration files (stores.txt and tables.txt)
#
# It is not 'necessary' to bind-mount or name-mount any of these directories,
# unless you wish to manipulate CINDI from the outside.

# --- TCP PORTS  ------
# CINDI's default listen port for the Flask HTTP Development server is 36963.  

# --- HOW TO USE ------
# 1) $ docker build -t cindi-lite .
# 2) $ docker run -dp 36963:36963 -v cindi-lite-data:/app/data -v cindi-lite-logs:/app/logs cindi-lite 
# 2a) adding a bind-mount for /app/config is an option, if you have the .txt's!
# 3) `docker exec -it` into the container, and populate with 'EXAMPLE' data:
# 3a) `$ python`
# 3b) `>>> import cindi`
# 3c) `>>> cindi.quick_unit_tests()`
# 3d) Verify the last line printed is 'True' which means all 17 tests passed!
#
# OR
#
# https://github.com/ultasun/cindi-lite

# ----------------------
# Beginning of the 'cindi-lite' Dockerfile.
# Please pull 'cindi' and examine /that/ Dockerfile, too -- it uses Debian.

# Use Official Python from Official Alpine
FROM python:alpine

# Update / Upgrade Alpine
RUN apk -U upgrade

# Warning, getting postgresql to work with python in alpine requires doing a
# multi-layer Dockerfile, please read:
# https://github.com/psycopg/psycopg2/issues/684
#RUN apk install libpq

# Upgrade pip
RUN pip install --upgrade pip

# most packages are not available in the test.pypi.org index.
# uncomment the next line if installing cindi from test.pypi.org
#RUN pip install psycopg ; pip install psycopg[pool] ; pip install redis ; pip install mysql-connector-python ; pip install flask ; pip install flask_cors; pip install pyOpenSSL ; pip install pymongo

# Install the CINDI pip package 
RUN pip install cindi

# Create a non-privileged user for the runtime, home directory /app
RUN adduser --disabled-password -h /app -s /bin/bash -u 36963 python-user

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
# End of the 'cindi-lite' Dockerfile
