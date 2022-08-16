# Cacheable Implementation Neutral Data Intermediate (CINDI)
#
# Read the LICENSE. Read the README. Thank you for reading.

# beginning of file cindi.py
# ------------------------------------------------------------------------------
# begin imports

# standard library imports
import base64
import json
import os
import traceback
import sys
import signal
import time
import traceback
import urllib

# third party imports
from flask import Flask, jsonify, request
from flask_cors import CORS

# attempt to import the MySQL connector library
try:
    import mysql.connector
    print('+++ MySQL support will be available.')
    DRIVER_AVAILABLE_MYSQL = True
except BaseException:
    print('--- MySQL support will not be available.')
    DRIVER_AVAILABLE_MYSQL = False

# attempt to load PostgreSQL library
try:
    import psycopg
    print('+++ PostgreSQL support will be available.')
    DRIVER_AVAILABLE_POSTGRESQL = True
except BaseException:
    print('--- PostgreSQL support will not be available.')
    DRIVER_AVAILABLE_POSTGRESQL = False

# attempt to load MongoDB library
try:
    import pymongo
    print('+++ MongoDB support will be available.')
    from pymongo import InsertOne, DeleteOne, DeleteMany, UpdateOne, UpdateMany
    DRIVER_AVAILABLE_MONGODB = True
except BaseException:
    print('--- MongoDB support will not be available.')
    DRIVER_AVAILABLE_MONGODB = False

# attempt to load Redis library
try:
    import redis
    print('+++ Redis support will be available.')
    DRIVER_AVAILABLE_REDIS = True
except BaseException:
    print('--- Redis support will not be available.')
    DRIVER_AVAILABLE_REDIS = False

# SQLite3 library is always available...
import sqlite3

# end imports
# ------------------------------------------------------------------------------
# begin constants delcarations section

DEBUG_PRINT_PREFIX__REDIS = "REDIS> "
DEBUG_PRINT_PREFIX__MYSQL = "MySQL> "
DEBUG_PRINT_PREFIX__MONGO = "mongodb> "
DEBUG_PRINT_PREFIX__POSTGRES = "postgres> "
DEBUG_PRINT_PREFIX__SQLITE3 = "sqlite3> "

ERROR__FIELDS_AND_VALUES_BAD_QUANTITY = """!! ERROR: 
The quantity of fields detected is not equal to the number of values detected.  
Check the CINDI README."""

# end constants declarations section
# ------------------------------------------------------------------------------
# begin domain-inspecific functions
# (these functions were written for CINDI but are not specific to CINDI)

def try_int(x):
    """
    Passes the argument into int() which resides in a try/except block.
    """
    try:
        return int(x)
    except:
        return x

def format_str_or_int(x):
    """
    Wrap str argument with quotes, unless is an int. Always returns a string.

    SQL and Redis statements should be given strings wrapped in quotes, and
    should be given integers without quotes. If this argument is given a string,
    then it will return the string with single-quotes padded; else, the integer
    will be returned as a string.
    """
    result_str = ''
    if isinstance(x, int):
        result_str = str(x)
    elif isinstance(x, str):
        result_str = "\'" + x + "\'"
    return result_str

def pairlis(list_a, list_b):
    """
    Similar to the Common Lisp pairlis function. Returns a list of tuples.

    This function will 'merge' the two lists together in sequential pairs.
    If one list is longer than the other, then the trailing list elements will
    be lost in the result. 
    """
    result = []
    for a, b in zip(list_a, list_b):
        result.append((a, b))
    return result

def is_list_all_nones(list):
    """
    Check if a 1D list contains all None elements. Returns a boolean.
    """
    if len(list) > 0:
        return (list[0] == None) and is_list_all_nones(list[1:])
    else:
        return True

def is_all_list_elements_equal(testList):
    """
    Check if a 1D list contains all equal elements. Returns a boolean.
    """
    list_count = len(testList)
    boolean_result = True
    
    if list_count > 1:
        for i in range (1, list_count):
            boolean_result = boolean_result and \
                testList[0] == testList[i]

    return boolean_result

def len_2d_list(two_dimensional_list):
    """
    Iterate through a 2D list and count the elements. Returns an integer.
    """
    result = 0
    for x in two_dimensional_list:
        for y in x:
            result += 1

    return result

def print_2d_list(two_dimensional_list):
    """
    Iterate through a 2D list, print the str() result of elements. Returns void. 
    """
    for x in two_dimensional_list:
        for y in x:
            print("-------------")
            print(str(y))
        print("-------------")

def print_3d_list(three_dimensional_list):
    """
    Iterate through a 3D list, print the str() result of elements. Returns void.
    """
    for x in three_dimensional_list:
        print("-------------")
        print_2d_list(x)
    print("-------------")

# https://stackoverflow.com/a/12517490
def fprint(string, label_prefix='', sub_directory='logs/', exit_on_fail=True):
    """
    Print a string to a nano-second-time-stamped file and close. Returns void.

    First argument is the string to print. Second argument is a prefix for the
    filename. Third argument is the sub-directory where to write the file, and
    if the sub-directory does not exist, then it will be created.

    !! Fourth argument (default True) specifies whether to EXIT THE PROCESS if
    the operation raises any exception. !!
    """
    try:
        now_ns = str(time.time_ns())
        filename = sub_directory + label_prefix + '_' + now_ns
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            f.write(string + '\n')
        f.close()
    except BaseException:
        print('fprint failed to print to file: ' + filename)
        print('fprint failed to print to file: ' + string)
        if exit_on_fail:
            exit(5) # 'input/output error'

# end domain-inspecific functions
# ------------------------------------------------------------------------------
# begin lower-order domain-specific functions
# (which apply to no particular driver)

def get_indi_fields(c):
    """
    Given an INDI statement c, return a list of the user supplied FIELDS.
    """
    if c.find('(') > 0 and c.find(')') > 0:
        result = c[(1 + c.find('(')):c.find(')')]
        result = result.split(', ')
        return result
    else:
        return [c.split()[-1]]

# requires the VALUES clause to have strings within double quotes,
# with a comma and space between elements. it specifically checks for a ", "
# between elements, so an input string is not allowed to contain this, or
# else it will trigger an ERROR__FIELDS_AND_VALUES_BAD_QUANTITY
def get_indi_values(c):
    """
    Given an INDI statement c, return a list of the user supplied VALUES.
    """
    first_l_parenthesis_index = c.find('(') + 1
    first_r_parenthesis_index = c.find(')') + 1
    values = c[(c.find('(', first_l_parenthesis_index) \
                + 1):c.find(')', first_r_parenthesis_index)]
    values = values.split("\", \"")
    values[0] = values[0].strip('\"')
    values[-1] = values[-1].strip('\"')
    return values

def get_indi_query(c):
    """
    Remove single/double quotes from an INDI query, if they exist. Returns str.
    """
    result = None
    
    if c.find('\"') > -1 and c.find('\"') < c.find('FIELDS'):
        result = c.split('\"')[1]
    elif c.find('\'') > -1 and c.find('\'') < c.find('FIELDS'):
        result = c.split('\'')[1]
    else:
        result = c.split()[4]
        
    return result

# end lower-order domain-specific functions
# ------------------------------------------------------------------------------
# begin Redis driver

# the following function is not actually used anywhere, but may come in handy.
def convert_to_redis__find_last_pk(read_only_redis, schema, table_name):
    """
    Find the last primary key used in redis for a given INDI table. Returns int.

    The same result may be achieved by subtracting one from the integer result
    of convert_to_redis__get_next_pk(). Please use that function, this function
    is an expensive search. Should only be used for verification/debugging.

    If modifying this function, please do not do any writing to read_only_redis,
    such writes should be performed within the execute_redis function.

    The first argument is a redis connection to help read values to answer
    questions. The second argument is the prefix for the redis key, and is the
    same value keyed by the 'db' key in stores.txt (under 'redis'). The third
    argument is the INDI table name.
    """
    result = 0
    primary_keys = []
    entire_table = read_only_redis.keys(schema + '-' + table_name + '_*_*')
    print(DEBUG_PRINT_PREFIX__REDIS \
          + "KEYS " + (schema + '-' + table_name + '_*_*'))
    for row_col in entire_table:
        this_key = int(row_col.decode('ASCII').split('_')[1])
        if this_key not in primary_keys:
            primary_keys.append(this_key)

    primary_keys.sort()

    if len(primary_keys) > 0: 
        result = primary_keys[-1]

    return result

def convert_to_redis__get_next_pk(read_only_redis, schema, table_name):
    """
    Retrieve the next primary key for this redis table. Returns an integer.

    The same result may be achieved by adding one from the integer result
    of convert_to_redis__find_last_pk(). Please do NOT use that function, since
    this function is an inexpensive quick look-up, as the value is stored in a
    redis key. 
    
    If modifying this function, please do not do any writing to read_only_redis,
    such writes should be performed within the execute_redis function.

    The first argument is a redis connection to help read values to answer
    questions. The second argument is the prefix for the redis key, and is the
    same value keyed by the 'db' key in stores.txt (under 'redis'). The third
    argument is the INDI table name.
    """
    result = read_only_redis.get(schema + '-' + table_name + '-NEXTPK')
    print(DEBUG_PRINT_PREFIX__REDIS \
          + "GET " + (schema + '-' + table_name + '-NEXTPK'))
    if result is None:
        result = 1
    return int(result)

def convert_to_redis__set_next_pk(schema, table_name, last_used_pk):
    """
    Compose the redis statement to SET the next primary key. Returns a string.

    Note that this function only returns a string, it does not perform the
    operation. The result of this function is used in execute_redis.

    The first argument is the prefix for the redis key, and is the same value
    keyed by the 'db' key in stores.txt (under 'redis'). The second argument is
    the INDI table name. The third argument is the last used primary key.
    """
    return 'SET ' \
        + schema + '-' + table_name + '-NEXTPK ' + str(int(last_used_pk) + 1)

# remember, we only need `read_only_redis` in order to emulate
# sub-queries, in particular, for DELETE, because you can not
# wildcard delete keys in Redis.
#
# please do NOT break the paradigm and issue any mutating commands
# => !! only do KEYS and GET commands please with read_only_redis !!!!!!! <=
# => !! the SET commands are supposed to happen later in execute_redis !! <=
def convert_to_redis(c, stores):
    """
    Convert an INDI statement to redis statements. Returns multiple values.

    The first value returned is a list of strings which contain the resulting
    redis statements. The second value is a list of strings which contain the
    FIELDS from the original INDI statement.

    More than likely, it will take many redis statements to emulate a single
    INDI statement. This function returns the list of equivalent redis code. 
    
    The first argument is the INDI statement (a string) to convert.
    The second argument is the stores dictionary, which is the result of
    initialize_stores().

    The stores are passed as an argument in order to emulate sub-queries. The
    stores are not supposed to be written to within this function.
    
    !! If you are modifying this function, please do not execute any 'write'
    style commands on read_only_redis. Instead, place the write into the result
    of this function. !! 
    """
    read_only_redis = stores['redis'] # no way to enforce 'read only'
    schema = stores['info']['redis']['db']
    results = []
    c_array = c.split()
    fields = None
    matching_pk_list = [] # used for the single-depth subquery 
    
    if c_array[0].upper() == 'DELETE':
        fields = [''] # convertToRedis_getFields probably crashes for a DELETE
    else:
        fields = get_indi_fields(c) 

    # *** "FIRST",    
    # in order to support querying by more than just the ID integer
    # we need to do a sub-query, in order
    # to find the ID, this way we do not have to modify any code we wrote,
    # and instead we will substitute the query
    if c_array[0].upper() != 'CREATE' \
       and (c_array[3].lower() != 'id' and c_array[3].upper() != 'ALL'): 
        search_by_field = c_array[3]
        search_by_value = get_indi_query(c)
        
#        if c.find("\"") > -1 and c.find("\"") < c.find('FIELDS'):
#            search_by_value = c.split("\"")[1]
#        elif c.find("\'") > -1 and c.find("\'") < c.find('FIELDS'):
#            search_by_value = c.split("\'")[1]
#        else:
#            search_by_value = c_array[4]

        # need to update the next line so c_array[3] is search_by_value
        # because otherwise the quotes will be passed in
        matching_keys = read_only_redis.keys((schema + '-' + \
                                              c_array[2]) + \
                                             '_*_' + c_array[3])

        print(DEBUG_PRINT_PREFIX__REDIS + \
              "matching key length: " + str(len(matching_keys)))
        # this returns every row in the table,
        # only the ID and search_by_field columns...use the redis SCAN command
        for m in matching_keys: 
            print(DEBUG_PRINT_PREFIX__REDIS + "GET " + m.decode('ASCII'))
            this_value = read_only_redis.get(m)
            print(DEBUG_PRINT_PREFIX__REDIS + \
                  this_value.decode('ASCII') + \
                  " compared to " + search_by_value)
            if this_value.decode('ASCII') == search_by_value:
                matching_pk_list.append(m.decode('ASCII').split('_')[1])

        if(len(matching_pk_list) == 0):
            return [], fields # the record was not found
        else:
            matching_pk_list.sort() # may be out-of-order numerically

    # *** "SECOND",
    # evaluate the INDI statement 
    if c_array[0].upper() == 'READ':
        # pulling all records
        if c_array[3] == 'ALL' and c_array[4] == 'RECORDS':
            max_pk = convert_to_redis__get_next_pk(read_only_redis, \
                                             schema, c_array[2])
            print(DEBUG_PRINT_PREFIX__REDIS + "max_pk is: " + str(max_pk))
            for i in range(1, max_pk):
                for field in fields:
                    results.append('GET ' + (schema + '-' + c_array[2]) \
                                   + '_' + str(i) + '_' + field)
                    
        # pulling records which match a query
        else:
            if len(matching_pk_list) == 0:
                matching_pk_list.append(c_array[4])
                
            for pk in matching_pk_list:
                for field in fields:
                    results.append('GET ' + (schema + '-' + c_array[2]) \
                               + '_' + pk + '_' + field)
                
    elif c_array[0].upper() == 'UPDATE':
        values = get_indi_values(c)
        # the string tokenization ought to be replaced with regex
        # or maybe the user submitted an invalid DML statement
        if len(fields) != len (values): 
            return ERROR__FIELDS_AND_VALUES_BAD_QUANTITY

        # if the DML is to update just one thing by the pk, then
        # matching_pk_list is empty so far
        if len(matching_pk_list) == 0:
            matching_pk_list.append(c_array[4])
            
        for pk in matching_pk_list:
            for i in range(0, len(fields)):
                results.append('SET ' + (schema + '-' + c_array[2]) + '_' \
                           + pk + '_' + fields[i] + ' ' \
                           + format_str_or_int(values[i])) 

    elif c_array[0].upper() == 'CREATE':
        values = get_indi_values(c)
        # if a user stores a string in here in a certain format, maybe errors?
        if len(fields) != len(values): 
            return ERROR__FIELDS_AND_VALUES_BAD_QUANTITY

        this_new_pk = convert_to_redis__get_next_pk(read_only_redis, \
                                             schema, c_array[2])
        fields.append('id')
        values.append(this_new_pk)

        results.append(\
                convert_to_redis__set_next_pk(schema, c_array[2], this_new_pk))
        
        for i in range(0, len(fields)):
            results.append('SET ' + (schema + '-' + c_array[2]) + '_' \
                           + str(this_new_pk) + '_' + fields[i] + ' ' \
                           + format_str_or_int(values[i]))

    elif c_array[0].upper() == 'DELETE':
        matching_keys = []

        # the query may have specified the pk, so matching_pk_list
        # would be empty (because there was no subquery search)
        if len(matching_pk_list) == 0 and c_array[3] == 'id':
            matching_pk_list.append(c_array[4])
            
        for pk in matching_pk_list: 
            these_matching_keys = \
                    read_only_redis \
                    .keys((schema + '-' \
                           + c_array[2]) \
                          + '_' + pk \
                          + '_*')
            # need to 'flatten the list'
            for k in these_matching_keys:
                matching_keys.append(k)
                
        for m in matching_keys:
            results.append('DEL ' + m.decode('ASCII'))
            print(DEBUG_PRINT_PREFIX__REDIS + 'DEL ' + m.decode('ASCII'))

    # "THIRD",
    # return the list of INDI statements converted to redis commands,
    # and the INDI FIELDS specified from the original INDI statement.
    return results, fields

def execute_redis(indi_statement, stores):
    """
    Execute an INDI statement against redis. Returns a multi-dimensional list.

    The first argument is the indi_statement, as a string. The second argument
    is the stores dictionary as created by initialize_stores().  
    
    The only time the result should have any real values in it would be from
    an INDI read statement. Any CREATE, UPDATE, DELETE INDI statement should
    return an empty list.
    """
    results = []
    converted_to_redis, fields = convert_to_redis(indi_statement, stores)

    # the string tokenization may have failed, a better solution
    # might involve the use of regular expressions? 
    if converted_to_redis == ERROR__FIELDS_AND_VALUES_BAD_QUANTITY:
        print(ERROR__FIELDS_AND_VALUES_BAD_QUANTITY)
        exit(52) # 'common linux error: invalid exchange'
    
    set_length = len(fields) # only need the quantity of fields
    this_built_set = []
    redis_connection = stores['redis']
    
    for statement in converted_to_redis:
        # there is a lack-of-ability in the python redis client library,
        # it is unable to 'raw parse' a full redis statement, but it as been
        # added to future features 'maybe', so perhaps then the code here
        # may be simplified...pertaining to redis_command and redis_key.  
        # see https://github.com/redis/redis-py/issues/1659
        print(DEBUG_PRINT_PREFIX__REDIS + statement)
        redis_command = statement.split()[0].upper()
        redis_key = statement.split()[1]
        if "\"" in statement or "'" in statement:
            redis_value = statement[len(redis_command) + len(redis_key) \
                                   + 3 : len(statement)-1]
        else:
            redis_value = statement[len(redis_command) + len(redis_key) \
                                   + 2 : len(statement)] 
            this_result = None

        if statement.split()[0].upper() == 'SET':
            print(DEBUG_PRINT_PREFIX__REDIS + redis_key + " " + redis_value)
            if redis_connection.set(redis_key, redis_value):
                this_result = None
            else:
                this_result = "Redis SET failed. Check the CINDI README."
                print(DEBUG_PRINT_PREFIX__REDIS + this_result)
                print(DEBUG_PRINT_PREFIX__REDIS + \
                      'This was the statement to evaluate: ')
                print(DEBUG_PRINT_PREFIX__REDIS + statement)
                exit(29) # 'cannot write to specified device' 
        else:
            this_result = redis_connection.execute_command(statement)
            # a 'DEL' will return a 1 into this_result, desire 'None'
            if statement.startswith('DEL'):
                this_result = None

        if not this_result is None:
            if isinstance(this_result, int):
                this_built_set.append(this_result)
            else:
                maybeAnInt = try_int(this_result.decode('ASCII'))
                this_built_set.append(maybeAnInt)
        else:
            this_built_set.append(None)

        print(DEBUG_PRINT_PREFIX__REDIS + \
              "redis this built set length: " + str(len(this_built_set)))
        for x in this_built_set:
            print(DEBUG_PRINT_PREFIX__REDIS +
                  "redis set element: " + str(x))
            
        if len(this_built_set) == set_length:
            if not is_list_all_nones(this_built_set):
                results.append(this_built_set)
            this_built_set = []
        
    return results

# end redis driver
# ------------------------------------------------------------------------------
# begin generic SQL driver
# a future version of this might use SQLAlchemy, but my intuition tells me
# avoiding SQLAlchemy might result in overall less instructions for the CPU,
# and my intution tells me converting INDI statements to work with SQLAlchemy
# would be awkward. 

def convert_to_sql__fields_merger(field_list):
    """
    Convert a list of strings into a comma-separated-value. Returns a string.

    Example: `['a', 'b', 'c']` becomes `'a, b, c'`
    """
    result_str = ''
    for i in range(0, len(field_list)-1):
        result_str += field_list[i] + ', '
    result_str += field_list[-1]
    return result_str

# there is a one-to-one mapping between INDI and SQL statements
# to keep it consistent, it still returns a list (containing one statement)
def convert_to_sql(c):
    """
    Convert an INDI statement into an SQL statement. Returns a string in a list.

    This process is simple, because the INDI language is nearly a subset of SQL
    with the statement sub-components ordered differently. 
    """
    results = []
    c_array = c.split()

    SQL__PK_COLUMN_NAME = c_array[3]
    
    if c_array[0].upper() == 'READ':
        fields = get_indi_fields(c)

        if c_array[3].upper() == 'ALL' and c_array[4].upper() == 'RECORDS':
            results.append('SELECT ' + convert_to_sql__fields_merger(fields) \
                           + ' FROM ' + (c_array[2]) \
                           + ' ORDER BY id ASC;')
            
        else:
            query_by_value = get_indi_query(c)
            #if c.find("\"") > -1 and c.find("\"") < c.find('FIELDS'):
            #    query_by_value = c.split("\"")[1]
            #elif c.find("\'") > -1 and c.find("\'") < c.find('FIELDS'):
            #    query_by_value = c.split("\'")[1] 

            results.append('SELECT ' +  convert_to_sql__fields_merger(fields) \
                           + ' FROM ' + (c_array[2]) \
                           + ' WHERE ' + SQL__PK_COLUMN_NAME + ' = ' \
                           + format_str_or_int(try_int(query_by_value))
                           + ' ORDER BY id ASC;')

    elif c_array[0].upper() == 'CREATE':
        fields = get_indi_fields(c)
        values = get_indi_values(c)
        # the string tokenization used might not be perfect, so need to check
        if len(fields) != len(values):
            return ERROR__FIELDS_AND_VALUES_BAD_QUANTITY

        result_str = 'INSERT INTO ' + (c_array[2]) + ' ('
        for i in range(0, len(fields)-1):
            result_str += fields[i] + ', '

        result_str += fields[-1] + ')'

        result_str += ' VALUES ('
        for i in range(0, len(values)-1):
            result_str += format_str_or_int(values[i]) + ', '

        result_str += format_str_or_int(values[-1])
        result_str += ');'

        results.append(result_str)
    elif c_array[0].upper() == 'UPDATE':
        fields = get_indi_fields(c)
        values = get_indi_values(c)
        
        # the string tokenization used might not be perfect, so double check
        if len(fields) != len(values): 
            return ERROR__FIELDS_AND_VALUES_BAD_QUANTITY

        query_by_value = get_indi_query(c)
        #if c.find("\"") > -1 and c.find("\"") < c.find('FIELDS'):
        #    query_by_value = c.split("\"")[1]
        #elif c.find("\'") > -1 and c.find("\'") < c.find('FIELDS'):
        #    query_by_value = c.split("\'")[1]
            
        result_str = 'UPDATE ' + (c_array[2]) + ' SET '
        for i in range(0, len(values) - 1):
            result_str += fields[i] + ' = ' + format_str_or_int(values[i]) \
                + ', '

        result_str += fields[-1] + ' = ' + format_str_or_int(values[-1])        
        result_str += ' WHERE ' + SQL__PK_COLUMN_NAME + ' = ' \
            + format_str_or_int(try_int(query_by_value)) + ';'
        results.append(result_str)

    elif c_array[0].upper() == 'DELETE':
        query_by_value = get_indi_query(c)
#        if c.find("\"") > -1 and c.find("\"") < c.find('FIELDS'):
#            query_by_value = c.split("\"")[1]
#        elif c.find("\'") > -1 and c.find("\'") < c.find('FIELDS'):
#            query_by_value = c.split("\'")[1]
#        else: # the next line did a forced cast to int() previously...
#            queryByvalue = try_int(query_by_value)
            
        result_str = 'DELETE FROM ' + (c_array[2]) + ' WHERE ' \
            + SQL__PK_COLUMN_NAME + ' = ' \
            + format_str_or_int(try_int(query_by_value))
        results.append(result_str)
        
    return results

def execute_sql(statements, stores, DEBUG_PREFIX):
    """
    Execute SQL statements. Returns a multi-dimensional list of query results.

    The first argument should be a list of valid SQL strings. The second
    argument is the dictionary of connections created by initialize_stores().
    The third argument is very important, it's how this function determines
    which driver to use in stores, and is also used to print debug messages.
    See the DEBUG_PRINT_PREFIX variables in the constant declarations section
    above.

    Due to the homoiconicity of the various SQL implementations available in
    python, this function may be regarded as a generic function.
    """
    driver_name = DEBUG_PREFIX.split(">")[0].lower()
    sql_connection = stores[driver_name]
    results = []
    for statement in statements:
        print(DEBUG_PREFIX + statement)

        this_cursor = sql_connection.cursor()
        this_cursor.execute(statement)
        print(DEBUG_PREFIX \
              + "result row count " + str(this_cursor.rowcount))
        
        # no .fetchAll() because that might slow us down...
        try:
            for row in this_cursor:
                this_row_result = []
                for column in row:
                    if not isinstance(column, int):
                        try:
                            column = column.decode('ASCII')
                        except AttributeError:
                            column = column

                    print(DEBUG_PREFIX + str(column))
                    this_row_result.append(column)
                if not is_list_all_nones(this_row_result):
                    results.append(this_row_result)
        
        # execute_postgres recycles this function, but it
        # throws a psycopg.ProgrammingError exception after an INSERT
        # upon starting the `for row in this_cursor`... even though
        # this_cursor.rowcount > 0. so, without naming a specific
        # exception related to postgres in the mysql definition driver,
        # it is more general to return an empty result set (for now).
        except:
            results = []
        
        this_cursor.close()
        sql_connection.commit()

    return results

# end generic SQL driver 
# ------------------------------------------------------------------------------
# begin MySQL driver 

def execute_mysql(statement, stores):
    """
    Run an INDI statement on a MySQL store. Returns a multi-dimensional list.

    The first argument is the INDI statement as a string, the second is the
    python dictionary of stores.

    This function subcontracts nearly all the work to convert_to_sql and
    execute_sql.
    """
    converted_statements = convert_to_sql(statement)
    return \
        execute_sql(converted_statements, stores, \
                             DEBUG_PRINT_PREFIX__MYSQL)

# end MySQL driver
# ------------------------------------------------------------------------------
# begin PostgreSQL driver
# https://www.psycopg.org/psycopg3/docs/basic/index.html

def execute_postgres(statement, stores):
    """
    Run an INDI statement on a PostgreSQL store. Returns multi-dimensional list.

    The first argument is the INDI statement as a string, the second is the
    python dictionary of stores.

    This function subcontracts nearly all the work to convert_to_sql and
    execute_sql.
    """
    converted_statements = convert_to_sql(statement)
    return \
        execute_sql(converted_statements, stores, \
                               DEBUG_PRINT_PREFIX__POSTGRES)

# end PostgreSQL driver
# ------------------------------------------------------------------------------
# begin sqlite3 driver 

def execute_sqlite3(statement, stores):
    """
    run an INDI statement on a Sqlite3 store. Returns a multi-dimensional list.

    The first argument is the INDI statement as a string, the second is the
    python dictionary of stores.

    This function subcontracts nearly all the work to convert_to_sql and
    execute_sql.
    """
    converted_statements = convert_to_sql(statement)
    return \
        execute_sql(converted_statements, stores, \
                               DEBUG_PRINT_PREFIX__SQLITE3)

# end sqlite3 driver
# ------------------------------------------------------------------------------
# begin MongoDB driver

# returns the next primary key to be used, which is an integer
# (so, if you are wondering what the 'highest used' pk is, then subtract one.)
def convert_to_mongo__get_next_pk(db, group_name):
    """
    Determine the next primary key for the INDI table. Returns an integer.

    The first argument is the mongo database object, the second argument is the
    group_name (which is the INDI table name).

    This does not write to the database, it only calculates what the next
    primary key would be.
    
    MongoDB doesn't use 'tables' for anything (unlike SQL systems), so in this
    mongo driver, they will be referred to as the 'group' or 'group_name'.
    """
    objects_pk = db.objects_pk
    next_pk = db.objects_pk.find_one({'primary-key-object': True, \
                                      'group': group_name})
    
    if isinstance(next_pk, dict) and 'next_pk' in next_pk:
        return next_pk['next_pk']
    else: # this happens if the database is empty, so next_pk is 1.
        return 1

# this will mutate 'next_pk' in the database to increment by 1
def convert_to_mongo__create_new_pk(db, c_array):
    """
    Increment the INDI table pk by one. Returns an integer.

    The first argument is the mongo database object. The second argument is the
    tokenized INDI statement.
    """
    objects_pk = db.objects_pk
    group_name = c_array[2]

    next_pk = convert_to_mongo__get_next_pk(db, group_name)

    # increment the next_pk by 1, could have used $inc maybe?
    db.objects_pk.bulk_write([UpdateOne( \
                                    {'group': group_name, \
                                     'primary-key-object': True}, \
                                    {'$set': \
                                     { 'next_pk': (next_pk + 1)}}, \
                                       upsert=True)])

    # things are easier during queries if this is a string
    return str(next_pk)

# added group_name, it might have broke it.
def convert_to_mongo__find_primary_keys(\
        db, group_name, search_by_field, search_by_value, return_ints=False):
    """
    Find the primary keys associated with a field/value pair. Returns a list.

    The first argument is the mongo database object. The second argument is a
    string containing the group (INDI table) name. The third argument is a
    string containing the field to search by. The fourth argument is the value
    to search by. The fifth optional argument specifies whether or not to
    cast the results to integers befor appending to the result list, which
    is False by default.
    """
    objects = db.objects
    results = []

    for row in objects.find({
            'group': group_name, \
            'field': search_by_field, \
            'value': search_by_value}):
        if return_ints:
            results.append(int(row['id']))
        else:
            results.append(row['id'])

    return results

# "Bulk Write Operations" example here:
# https://pymongo.readthedocs.io/en/stable/examples/bulk.html
def convert_to_mongo(c, stores):
    """
    Transfer INDI statement into MongoDB ops. Returns multi-dimensional list.

    The author accidentally wrote the entire process in this function, and the
    parent execute_mongo doesn't do much besides filter out results from
    CREATE/UPDATE/DELETE 
    """
    schema = stores['info']['mongodb']['db']
    results = []
    c_array = c.split()
    
    db = stores['mongodb'][schema]
    objects = db.objects
    group_name = c_array[2] # group_name is the 'table' (in SQL terms)

    if c_array[0].upper() == 'READ':
        fields_requested = get_indi_fields(c)
        if c_array[3].upper() == 'ALL' and c_array[4].upper() == 'RECORDS':
            matching_keys = range(1, \
                                  convert_to_mongo__get_next_pk(db, group_name))
        
        # query for a specific value in a specific field
        else:
            group_name = c_array[2]
            query_by_field = c_array[3]
            query_by_value = get_indi_query(c)

            # clean out any single or double quotes from the user
#            if c.find("\"") > -1 and c.find("\"") < c.find('FIELDS'):
#                query_by_value = c.split("\"")[1]
#            elif c.find("\'") > -1 and c.find("\'") < c.find('FIELDS'):
#                query_by_value = c.split("\'")[1]

            # added group_name, it might have broke it
            matching_keys = \
                convert_to_mongo__find_primary_keys(\
                    db, group_name, query_by_field, query_by_value)

        for pk_index in matching_keys:
            this_result = []
            cursor = objects.find({'group': group_name, 'id': str(pk_index)})
            for field in fields_requested:
                this_start_length = len(this_result)
                cursor.rewind() # recycling cursor for each field
                for record in cursor:
                    if record['field'] == field:
                        this_result.append(try_int(record['value']))
                # if the field's value was null, so to say...
                if this_start_length == len(this_result):
                    this_result.append(None)
            # if a 'row' was hit, which had been previously deleted....
            if len(this_result) > 0 and not is_list_all_nones(this_result):
                results.append(this_result)

    elif c_array[0].upper() == 'CREATE':
        new_pk = convert_to_mongo__create_new_pk(db, c_array)
        field_value_pairs = [('id', new_pk)]
        for key_value_tuple in pairlis( \
                                 get_indi_fields(c), \
                                 get_indi_values(c)):
            print(DEBUG_PRINT_PREFIX__MONGO \
                  + "mongo queuing for insertion " + str(key_value_tuple))
            field_value_pairs.append(key_value_tuple)

        # both storing the id as a 'field', and,
        # storing the id as a mongo field, is synonymous with
        # what the redis driver does...
        # (...it does things like `db0-nonsense_1_id`, that key would
        # hold the value '1', even though the value is in the key name
        
        for field_value_pair in field_value_pairs:
            print(DEBUG_PRINT_PREFIX__MONGO \
                  + "mongo collection insertion " + str(field_value_pair))
            results.append( \
                        db.objects.bulk_write([ \
                            InsertOne( \
                                       { \
                                         'id': new_pk, \
                                         'group': group_name, \
                                         'field': field_value_pair[0], \
                                         'value': field_value_pair[1] })]))

    elif c_array[0].upper() == 'UPDATE':
        group_name = c_array[2]
        field_to_search = c_array[3]
        value_of_field_to_search = get_indi_query(c)

        # clean out any single or double quotes from the user
#        if c.find("\"") > -1 and c.find("\"") < c.find('FIELDS'):
#            value_of_field_to_search = c.split("\"")[1]
#        elif c.find("\'") > -1 and c.find("\'") < c.find('FIELDS'):
#            value_of_field_to_search = c.split("\'")[1]

        print(DEBUG_PRINT_PREFIX__MONGO + " UPDATE by " \
              + value_of_field_to_search)
        
        field_value_pairs = pairlis( \
                                   get_indi_fields(c), \
                                   get_indi_values(c))

        if field_to_search == 'id':
            pk_list = [ value_of_field_to_search ]
        else:
            pk_list = convert_to_mongo__find_primary_keys( \
                db, group_name, field_to_search, value_of_field_to_search)

        # need upsert=True or else None fields will stay None!
        for pk in pk_list:
            print(DEBUG_PRINT_PREFIX__MONGO + "UPDATE pk " + pk)
            for field_value_pair in field_value_pairs:
                print(DEBUG_PRINT_PREFIX__MONGO + " pair " \
                      + str(field_value_pair))
                results.append( \
                    db.objects.bulk_write([ \
                        UpdateOne( \
                            { 'group': group_name, \
                              'id': pk, \
                              'field': field_value_pair[0] },
                            { '$set': \
                              { 'value': field_value_pair[1] }}, upsert=True)]))
                    
    elif c_array[0].upper() == 'DELETE':
        # need to find primary key of the entry and delete all records
        field_to_search = c_array[3]
        value_of_field_to_search = get_indi_query(c)

        # if the primary key was the query, then delete just that 'row'
        if field_to_search == 'id':
            results.append( \
                        db.objects.bulk_write([ \
                            DeleteMany({ \
                                'id': value_of_field_to_search, \
                                'group': group_name })]))
        # if the query was anything else, there could be multiple rows
        else:
            results.append( \
                        db.objects.bulk_write([ \
                            DeleteMany({ \
                                'group': group_name, \
                                'field': field_to_search, \
                                'value': value_of_field_to_search })]))

    return results

def execute_mongo(c, stores):
    """
    Evaluate the INDI statement into MongoDB. Returns a list.

    The first argument is the INDI statement. The second argument is the
    stores dictionary provided by initialize_stores().
    
    A multi-dimensional list in 'result set' style is returned if the INDI
    statement was a 'READ'. Else, it will return an empty list for CREATE,
    UPDATE or DELETE.

    Otherwise, this function sub-contracts nearly all the work to the child
    function, convert_to_mongo().

    In the future, convert_to_mongo() should return a list of mongo operations,
    and those mongo operations should be processed in this function. Such a
    change wouldn't be visible to the user anyway, and would only improve on
    code readability.
    """
    c_array = c.split()
    op_results = convert_to_mongo(c, stores)
    
    if not c_array[0].upper() == 'READ':
        return []
    
    return op_results

# end MongoDB driver
# ------------------------------------------------------------------------------
# begin higher-order domain-specific functions

def execute_indi(statement, stores=None, which_store='all'):
    """
    Execute an INDI statement on the stores. Returns a multidimensional list.

    First argument is the INDI statement. Second argument is the dictionary of
    stores, generated by initialize_stores(). Third argument is which store to
    apply the effect to.

    Default second argument is None, and it will initialize the stores for
    the user. Default third argument is 'all', which means to evaluate against
    all stores if desired.

    This system may be used against just one store if so desired, so that's why
    it's possible to specify which_store to use. But, if the system is used
    this way, it is not possible to go back to using 'all' stores without
    manually executing past CREATE/UPDATE/DELETE statements against the
    remaining stores. Else, the system will throw AssertionErrors.
    """
    result = []
    stores_was_none = False
    if which_store.lower() == 'all':
        # first, record the INDI statement to logs/, if is a DML/DQL statement
        if not statement.split()[0] == 'READ':
            fprint(statement, 'indi')
        # second, begin evaluating the statement through each active store
        for k in stores.keys():
            if k.lower() == 'info':
                continue
            else:
                result.append(execute_indi(statement, stores, k))
    else:
        # user is probably not invoking execute_indi with a None store
        if stores == None: # but just in case...
            stores = initialize_stores() # (user probably called quick_cindi)
            stores_was_none = True
        
        if which_store.lower() == 'mysql':
            result.append(execute_mysql(statement, stores))
        elif which_store.lower() == 'redis':
            result.append(execute_redis(statement, stores))
        elif which_store.lower() == 'postgres':
            result.append(execute_postgres(statement, stores))
        elif which_store.lower() == 'mongodb':
            result.append(execute_mongo(statement, stores))
        elif which_store.lower() == 'sqlite3':
            result.append(execute_sqlite3(statement, stores))
        else:
            result.append('invalid store specified in execute_indi()')

    # this is a good time to check if any of the data stores are corrupted
    if which_store.lower() == 'all' and not is_all_list_elements_equal(result):
        print("execute_indi> result before AssertionError:\n")
        print_3d_list(result)
        raise AssertionError(\
            "A result from one store is not like the others.")
    elif which_store.lower() == 'all':
        # verified that all stores returned the same data, so return one copy
        result = result[0]

    # if this function initialized the stores, then close them.
    if stores_was_none:
        close_stores(stores)
    
    return result

# figure out which primary 'id' keys are affected by a statement
# must not pass a None stores!
def find_affected_primary_keys(statement, stores, which_store='all'):
    """
    Find the primary keys related to an INDI statement. Returns a list.

    The first argument is an INDI statement (string), the second argument is
    a dictionary containing the stores (from initialize_stores()), and the
    third optional argument is which store to check.

    This system may be used against just one store if so desired, so that's
    why it's possible to specify which_store to use. But, if the system is
    used this way, it is not possible to go back to using 'all' stores without
    manually executing past CREATE/UPDATE/DELETE statements against the
    remaining stores. Else, the system will throw AssertionErrors.
    """
    result = []
    
    if which_store.lower() == 'all':
        for k in stores.keys():
            if k.lower() == 'info':
                continue
            else:
                result.append(find_affected_primary_keys(statement, stores, k))
    else:
        schema = stores['info'][which_store]['db']       
        c_array = statement.split()
        
        query_by_value = get_indi_query(statement)
#        if statement.find("\"") > -1 \
#           and statement.find("\"") < statement.find('FIELDS'):
#            query_by_value = statement.split("\"")[1]
#        elif statement.find("\'") > -1 \
#             and statement.find("\'") < statement.find('FIELDS'):
#            query_by_value = statement.split("\'")[1] 
        
        if which_store.lower() == 'mysql':
            search_cursor = stores['mysql'].cursor()
            search_cursor.execute('SELECT id FROM ' + c_array[2] + ' WHERE ' \
                                 + c_array[3] + ' = \'' + query_by_value \
                                 + '\' ORDER BY id ASC')
            for row in search_cursor:
                result.append(row[0])

        elif which_store.lower() == 'redis':
            search_redis = stores['redis']
            matching_keys = search_redis.keys((schema + '-' + c_array[2]) \
                                        + '_*_' + c_array[3])
            for k in matching_keys:
                this_value = search_redis.get(k)
                if this_value.decode('ASCII') == query_by_value:
                    result.append(int(k.decode('ASCII').split('_')[1]))
            result.sort()
        elif which_store.lower() == 'postgres':
            search_cursor = stores['postgres'].cursor()
            search_cursor.execute('SELECT id FROM ' + c_array[2] + ' WHERE ' \
                             + c_array[3] + ' = \'' + query_by_value \
                             + '\' ORDER BY id ASC')
            for row in search_cursor:
                result.append(row[0])
        elif which_store.lower() == 'mongodb':
            result = \
                convert_to_mongo__find_primary_keys(\
                    stores['mongodb'][schema], c_array[2], c_array[3], \
                        query_by_value, True)
        elif which_store.lower() == 'sqlite3':
            search_cursor = stores['sqlite3'].cursor()
            search_cursor.execute('SELECT id FROM ' + c_array[2] + ' WHERE ' \
                             + c_array[3] + ' = \'' + query_by_value \
                             + '\' ORDER BY id ASC')
            for row in search_cursor:
                result.append(row[0])
        else:
            result.append('invalid store for find_affected_primary_keys()')

    # this is a good time to check if any of the data stores are corrupted.
    if which_store.lower() == 'all' and not is_all_list_elements_equal(result):
        print("find_affected_primary_keys> result before AssertionError:\n" \
              + str(result))
        raise AssertionError(\
            "A list of primary keys from one store is not like the others.")
    elif which_store.lower() == 'all':
        # verified that all stores returned the same thing, so return just
        # one copy
        result = result[0]
    
    # don't want downstream users modifying 
    return tuple(result)

# same thing as execute_indi except it caches the result in a dictionary
# note this calls execute_indi to perform the DDL/DQL/DML action on the store
def execute_then_cache_indi(statement, caches, stores, which_store='all'):
    """
    Execute and cache an INDI statement. Returns a multi-dimensional list.

    The first argument is the INDI statement as a string, the second argument is
    the cache dictionary (as generated by initialize_cache()), the third
    argument is the stores dictionary, and the fourth optional argument is
    which store to evaluate the INDI statement on.

    This system may be used against just one store if so desired, so that's
    why it's possible to specify which_store to use. But, if the system is
    used this way, it is not possible to go back to using 'all' stores without
    manually executing past CREATE/UPDATE/DELETE statements against the
    remaining stores. Else, the system will throw AssertionErrors.    
    """
    stores_was_none = False
    
    result = None
    c_array = statement.replace('"', "'").split()

    # unpack the cache for this schema\table
    command = c_array[0].upper()
    table_name = c_array[2]
    cache = caches[table_name]
    
    if command == 'READ':
        if statement in cache:
            print('+ Cache hit! Query is \n\t' + statement)
            result = cache[statement][1] # "that was easy"
        else:
            print('+ Cache miss. Query is \n\t' + statement)
            if stores == None:
                stores = initialize_stores()
                stores_was_none = True
                
            # the DQL is an "ALL RECORDS" query to dump the entire table
            if c_array[3].upper() == 'ALL' and c_array[4].upper() == 'RECORDS':
                affected_pk_tuple = (0,) # the entire table 
            else:
                affected_pk_tuple = \
                    find_affected_primary_keys(statement, stores, which_store)
            read_result = execute_indi(statement, stores, which_store)
            cache[statement] = (affected_pk_tuple, read_result)
            result = read_result
    else:
        del_list = []
        if stores == None:
            stores = initialize_stores()
            stores_was_none = True
        if command == 'CREATE':
            print('+ Deleting cached ALL RECORDS statement, for ' + statement)
            del_list = []
            # search for DQL's with tables to be affected by this 'CREATE'
            for dql in cache.keys():
                if cache[dql][0] == (0,) and \
                   table_name == dql.split()[2] : # an 'ALL RECORDS' statement?
                    del_list.append(dql)
            # run the CREATE
            result = execute_indi(statement, stores, which_store)
        elif command == 'UPDATE' or command == 'DELETE':
            affected_pk_tuple = \
                find_affected_primary_keys(statement, stores, which_store)
            del_list = []
            # expensive O(n^2), but there could be many cached READ's affected!
            for affected_pk in affected_pk_tuple:
                for dql in cache.keys():
                    if (affected_pk in cache[dql][0] or cache[dql][0] == (0,)) \
                       and dql.split()[2] == table_name:
                        del_list.append(dql)     
            # run the UPDATE
            result = execute_indi(statement, stores, which_store)
        else:
            print('+ Invalid INDI command: ' + statement)
            result = [ 'Invalid INDI command.', statement ]
            
        # ? if the execute_indi fails, the cache might not be deleted, keep
        # this in mind when making CINDI fault-tolerant later!
        if len(del_list) > 0:
            # delete the found cached DQL's
            for dql in del_list:
                if dql in cache: # it may have been deleted already
                    print('+ Deleting cached DQL result \n\t ' \
                      + dql + ' \n\tBecause it is affected by \n\t ' \
                           + statement)
                    del cache[dql]

    # close the stores if necessary
    if stores_was_none:
        close_stores(stores)

    return result

# is statement likely to be an INDI statement?
# this does not verify 100% that the syntax is valid.
def is_indi_statement(statement):
    """
    Does the passed argument string resemble an INDI? Returns a boolean.

    Warning, this is a cheap test, it does not perfectly identify whether a
    string is an INDI statement or not.
    """
    c_array = statement.split()
    return (c_array[0].upper() == 'READ' \
            or c_array[0].upper() == 'CREATE' \
            or c_array[0].upper() == 'UPDATE' \
            or c_array[0].upper() == 'DELETE') \
            and c_array[1].upper() == 'IN'

# end higher-order functions
# ------------------------------------------------------------------------------
# begin database and cache initialization section

# stores.txt contains the connection information for each underlying database
# system which should be used by cindi. 
def read_stores_dot_txt():
    """
    Read the configuration 'config/stores.txt' file. Returns a dictionary.

    Warning, this will exit if there is a failure parsing the file.
    """
    try:
        stores_dot_txt = open('config/stores.txt', 'r', encoding='utf-8')
        stores = eval(stores_dot_txt.read())
        stores_dot_txt.close()
        if not isinstance(stores, dict):
            raise TypeError('config/stores.txt not a dictionary.')
    except FileNotFoundError:
        print('config/stores.txt not found, please check the CINDI README.')
        exit(2) # "common exit code 2: no such file or directory"
    except (SyntaxError, TypeError, BaseException):
        print('config/stores.txt not a dictionary, check the CINDI README.')
        exit(61) # "common exit code 61: no data available"
    return stores

# the tables *could* be detected automatically via the initialization scripts
# (the various .SQL files, the mongodb .js file), but which would be chosen
# to dictate the tables used by cindi? also, maybe the user would want to 
# define tables in those initialization scripts which wouldn't be used by
# cindi.
#
# so with the above two considerations, it's better to ask the user to define
# in tables.txt which tables should be used by cindi, and those tables better
# be defined in each initialization script.
def read_tables_dot_txt():
    """
    Read the configuration 'config/tables.txt' file. Returns a list.

    Warning, this will exit if there is a failure parsing the file.
    """
    try:
        tables_dot_txt = open('config/tables.txt', 'r', encoding='utf-8')
        tables = eval(tables_dot_txt.read())
        tables_dot_txt.close()
        if not isinstance(tables, list) and not isinstance(tables, tuple):
            raise TypeError('config/tables.txt not list or tuple.')
    except FileNotFoundError:
        print('config/tables.txt not found, please check the CINDI README.')
        exit(2) # "common exit code 2: no such file or directory"
    except (SyntaxError, TypeError, BaseException):
        print('config/tables.txt must be list or tuple, check CINDI README.')
        exit(61) # "common exit code 61: no data available"
    return tables

def initialize_stores(exit_on_failure=True):
    """
    Initialize the database stores dictionary. Returns a dictionary.

    The optional boolean argument, set to True by default, determines if the
    process should exit if any of the connections fail to initialize.
    
    For each store defined in 'config/stores.txt', attempt to connect to the
    server/store it points to. If a supported store is ommited in the file,
    that's okay, it will not be initialized. If an unsupported store is
    referenced, that's okay too, it will not know to try to initialize it.
    """
    result = {}
    
    conns = read_stores_dot_txt()
    if not len(conns.keys()) > 0:
        print('No stores defined in config/stores.txt! Check CINDI README.')
        exit(61)

    # export stores.txt since most functions need the actual used db name 
    result['info'] = conns

    # postgres 
    try:
        if DRIVER_AVAILABLE_POSTGRESQL and 'postgres' in conns:
            postgres_string = \
                "host=" + conns['postgres']['host'] + " " + \
                "dbname=" + conns['postgres']['db'] + " " + \
                "user=" + conns['postgres']['user'] + " " + \
                "password= " + conns['postgres']['password'] + " "
            result['postgres'] =  psycopg.connect(postgres_string)
        elif not DRIVER_AVAILABLE_POSTGRESQL and 'postgres' in conns:
            raise BaseException('PostgreSQL library not installed.')
    except BaseException:
        print('Failed to initialize PostgreSQL connection.')
        if exit_on_failure:
            exit(49) # 'common error 49: protocol not attached'

    # mysql
    try:
        if DRIVER_AVAILABLE_MYSQL and 'mysql' in conns:
            result['mysql'] = mysql.connector.connect( \
                    host=conns['mysql']['host'], \
                    user=conns['mysql']['user'], \
                    password=conns['mysql']['password'], \
                    database=conns['mysql']['db'])
        elif not DRIVER_AVAILABLE_MYSQL and 'mysql' in conns:
            raise BaseException('MySQL library not installed.')
    except BaseException:
        print('Failed to initialize MySQL connection.')
        if exit_on_failure:
            exit(49) # 'common error 49: protocol not attached'

    # sqlite3
    try:
        if 'sqlite3' in conns:
            filename = conns['sqlite3']['sqlite3_file_prefix'] \
                + conns['sqlite3']['db'] + '.db'
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            result['sqlite3'] = sqlite3.connect(filename)
    except BaseException:
        print('Failed to initialize sqlite3 connection, file not found?')
        if exit_on_failure:
            exit(49) # 'common error 49: protocol not attached'
        
    # mongo
    try:
        if DRIVER_AVAILABLE_MONGODB and 'mongodb' in conns:
            mongo_uri = "mongodb://" + conns['mongodb']['user'] + \
                ":" + urllib.parse.quote(conns['mongodb']['password']) + \
                "@" + conns['mongodb']['host'] + \
                ":" + str(conns['mongodb']['port']) + \
                "/" + conns['mongodb']['db']
            result['mongodb'] = pymongo.MongoClient(mongo_uri)
        elif not DRIVER_AVAILABLE_MONGODB and 'mongodb' in conns:
            raise BaseException('MongoDB library not installed.')
    except BaseException:
        print('Failed to initialize MongoDB connection.')
        if exit_on_failure:
            exit(49) # 'common error 49: protocol not attached'

    # redis
    try:
        if DRIVER_AVAILABLE_REDIS and 'redis' in conns:
            result['redis'] = redis.Redis( \
                            host=conns['redis']['host'], \
                            port=conns['redis']['port'], \
                            db=conns['redis']['redisDb'])
        elif not DRIVER_AVAILABLE_REDIS and 'redis' in conns:
            raise BaseException('Redis library not installed.')
    except BaseException:
        print('Failed to initialize redis connection.')
        if exit_on_failure:
            exit(49) # 'common error 49: protocol not attached'

    # all desired connections initialized!
    return result

def close_stores(stores, which_store='all'):
    """
    Close the stores found in the stores dictionary. Returns void.

    The first argument is the stores dictionary, from initialize_stores().
    The second optional argument specifies which store to close.
    """
    if stores == None:
        print('WARNING: Invoked close_stores when stores=None !')
        return
    
    if which_store.lower() == 'all':
        for k in stores.keys():
            if k.lower() == 'info':
                continue
            else:
                close_stores(stores, k.lower())
    elif which_store.lower() == 'mysql':
        stores[which_store].close()
    elif which_store.lower() == 'redis':
        stores[which_store].close()
    elif which_store.lower() == 'postgres':
        stores[which_store].close()
    elif which_store.lower() == 'mongodb':
        stores[which_store].close()
    elif which_store.lower() == 'sqlite3':
        stores[which_store].close()
    else:
        print('invalid store ' + which_store + ' specified in close_stores()')  

# initialize the cache after checking config/tables.txt
def initialize_cache():
    """
    Returns a dictionary, for using with execute_then_cache_indi().

    The dictionary will have a slot for each INDI table specified in the
    configuration 'config/tables.txt' file. 
    """
    table_list = read_tables_dot_txt()
    return dict.fromkeys(table_list, {})

# end database and cache initialization section
# ------------------------------------------------------------------------------
# begin highest-level-execution section

# initialize / instantiate the global cache
global_caches = initialize_cache()

# quickly execute and cache an INDI statement against all stores
def quick_cindi(statement, \
                stores=None, caches=global_caches, exit_on_fail=True):
    """
    Evaluate an INDI statement through cache. Returns a multi-dimensional list.

    The first argument is the INDI statement (as a string) to evaluate.
    The second optional argument, a stores dictionary from initialize_stores().
    The third optional argument, a cache dictionary from initialize_cache().
    The fourth optional argument determines if a database connection failure
    will cause the system to exit, default behavior is True, because default
    behavior is to assert that all INDI statements are evaluated equally
    across all enabled stores.

    This function exists to provide an 'one argument' way of evaluating INDI
    statements, meanwhile handling all underlying issues in a presentable way.
    INDI statements may be evaluated in a more 'manual' fashion, using the
    execute_then_cache_indi() or execute_indi() functions.

    If the user intention is to only use a specific store whilst other stores
    are enabled, then execute the INDI statements through a lower function,
    either execute_indi() or execute_then_cache_indi(); since they have the
    which_store optional argument. Please carefully read the warning about
    manual use of the which_store optional argument if that is the intention!
    """
    result = []
    try:
        result = execute_then_cache_indi(statement, caches, stores)
    except AssertionError:
        print('Corrupted store, please file a bug. Check the CINDI README.')
        if exit_on_fail:
            exit(117) # 'common linux error 117: structure needs cleaning'
    except Exception as err:
        print('High level error: {}'.format(err))
        if exit_on_fail:
            exit(131) #' common linux error 131: state not recoverable'
    except BaseException as err:
        print('Low level error: {}'.format(err))
        if exit_on_fail:
            exit(22) # 'common linxu error 22: invalid argument'
#    except mysql.connector.Error as err:
#        print('MySQL error: {}'.format(err))
#        if exit_on_fail:
#            exit(131) # 'common linux error 131: state not recoverable'
#    except psycopg.OperationalError as err:
#        print('Postgres error: {}'.format(err))
#        if exit_on_fail:
#            exit(131) # 'common linux error 131: state not recoverable'
#    except sqlite3.Error as err:
#        print('sqlite3 error: {}'.format(err))
#        if exit_on_fail:
#            exit(131) # 'common linux error 131: state not recoverable'
#    except redis.exceptions.RedisError as err:
#        print('redis error: {}'.format(err))
#        if exit_on_fail:
#            exit(131) # 'common linux error 131: state not recoverable'
#    except pymongo.errors.PyMongoError as err:
#        print('mongodb error: {}'.format(err))
#        if exit_on_fail:
#            exit(131) # 'common linux error 131: state not recoverable'
#    except BaseException as err:
#        result = [ 'Unknown error while parsing INDI statement.', \
#                   statement, str(err) ]

    # docker compose needs some help nudging out the stdout buffer...
    sys.stdout.flush()
    
    return result

# end highest-level-execution section
# ------------------------------------------------------------------------------
# begin Flask HTTP end point section

def start_cindi_flask(tcp_port=36963, host_name='0.0.0.0', enable_ssl=False):
    """
    Start a Flask HTTPS end-point on /evaluate to process INDI over the web!

    The optional argument allows the user to specify a tcp_port to listen on.

    The SSL context is 'adhoc' which means it will generate a new certificate
    each time the server is restarted. The default development Flask server
    is used. 
    """
    # change later to a proper name as per
    #https://flask.palletsprojects.com/en/2.0.x/api/
    app = Flask(__name__)
    cors = CORS(app)

    @app.route('/', methods=['GET'])
    def homepage():
        return """<html>
    <head><title>POST an INDI statement!</title></head><body>
    <h3>Hello! Thank you for visiting CINDI!</h3><hr />
    <p>Please 'POST' an INDI statement to /evaluate!</p></body</html>"""

    @app.route('/evaluate', methods=['POST'])
    def evaluate():
        # they warned in the Flask api, in case a user uploads a binary file,
        # you'd better check the content_length. The submitted INDI statement
        # is probably not longer than 100k characters...
        if request.content_length > 100000:
            print('cindi> trashing '
                  + str(request.content_length) + ' long INDI!')
            too_long_error = """The submitted request is too long,
            and probably not a valid INDI statement."""
            return jsonify(too_long_error)

        string_request = request.get_data().decode('ASCII')
        string_respons = None
        cindi_response = None
    
        if is_indi_statement(string_request):
            print('cindi> ' + str(string_request))
            cindi_response = quick_cindi(string_request)
            print('cindi> ' + str(cindi_response))
            string_respons = json.dumps(cindi_response)
        else:
            print('cindi> invalid INDI statement submitted!\n'
                  + string_request)
            string_respons = 'error, see server log for more detail'

        response = jsonify(string_respons)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    # another option is ssl_context='adhoc'
    if enable_ssl:
        app.run(debug=True, \
                host=host_name, port=tcp_port, ssl_context='adhoc')
    else:
        app.run(debug=True, host=host_name, port=tcp_port)  

# https://kracekumar.com/post/54437887454/ssl-for-flask-local-development/
# https://www.codegrepper.com/code-examples/python/change+port+flask

# end Flask HTTP end point section
# ------------------------------------------------------------------------------
# end of file cindi.py
