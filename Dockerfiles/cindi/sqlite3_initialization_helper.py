# this is a helper script to create the sqlite3 database, used by docker.
# 
# this helper script is intended to be invoked by a docker-compose.yml file.
# check /app/bootloader.sh -- this script is only ran if that script detects 
# the docker container is being loaded for the 'first time'.
#
# otherwise, the user can use https://stackoverflow.com/a/2049137 to load,
# such as `cat init-nonsense-sqlite3.sql | sqlite3 db0.db`, but do not fail
# to match the sqlite3 database file name with what is specified within the
# config/stores.txt dictionary!

import os
import sqlite3
from cindi import read_stores_dot_txt, read_tables_dot_txt

def initialize_sqlite3(sqlite3_conn, filename):
    setup = []
    sql_file = open(filename)
    for line in sql_file:
        stripped = line.rstrip().lstrip()
        # the shortest valid sqlite3 statement might be 'IF X', 3 chars long
        if len(stripped) > 3:
            setup.append(stripped)
    sql_file.close()
    
    cursor = sqlite3_conn.cursor()
    result = []
    
    try:
        # double check that the sqlite3 database is empty
        # *** the next line is intended to fail!
        result = cursor.execute('SELECT * FROM ' + setup[0].split()[2] + ';')
        # if still in this try block, then 
        print('*** INITIALIZATION FAILURE: The sqlite3 database is not empty!')
    except sqlite3.OperationalError:
        print('*** Initializing sqlite3 database..', end='')
        for s in setup:
            sqlite3_conn.execute(s)
    finally:
        result = cursor.execute('SELECT * FROM ' + setup[0].split()[2] + ';')
        print('.sqlite3 database initialized successfully.')

    cursor.close()
    return result

# run the initializer
cninfo = read_stores_dot_txt()
tables = read_tables_dot_txt()
filename = './init-nonsense-sqlite3.sql'

sqlite_db_filename = cninfo['sqlite3']['sqlite3_file_prefix'] \
                + cninfo['sqlite3']['db'] + '.db'
os.makedirs(os.path.dirname(sqlite_db_filename), exist_ok=True)
sqlite3_conn = sqlite3.connect(sqlite_db_filename)
sqlite3_init_result = initialize_sqlite3(sqlite3_conn, filename)

sqlite3_conn.close()

# end of file sqlite3_initialization_helper.py
