# Example / Demo / Test program for CINDI
# ------------------------------------------------------------------------------
# This requires the 'nonsense' schema to be loaded into whichever stores are
# going to be used. The author provided the following 4 native schemas:
# * MongoDB    => init-nonsense-mongodb.js
# * MySQL      => init-nonsense-mysql.sql
# * PostgreSQL => init-nonsense-postgresql.sql
# * SQLite3    => init-nonsense-sqlite3.sql
#
# There is no 'Redis' schema because the INDI engine handles the addition and
# removal of keys.
#
# !!! The user MUST manually load the schemas for each store before !!!
# !!! attempting to run the tests! Otherwise, the tests will fail.  !!!
#
# beginning of cindi_tests.py
# ------------------------------------------------------------------------------
# begin imports

from cindi import *

# end imports 
# ------------------------------------------------------------------------------
# begin examples declarations section
# remember, this is INDI, not SQL. 

# DML examples ('CREATE')
EXAMPLE0 = """CREATE IN nonsense FIELDS (nonsense_a, nonsense_b, nonsense_c) VALUES (\"hekkin big\", \"skare\", \"today and now\")"""
EXAMPLE1 = """CREATE IN nonsense FIELDS (nonsense_a) VALUES (\"yeah, right\")"""
EXAMPLE2 = """CREATE IN nonsense FIELDS (nonsense_b) VALUES (\"where is...\")"""
EXAMPLE3 = """CREATE IN nonsense FIELDS (nonsense_c) VALUES (\"will I ever find...\")"""
EXAMPLE4 = """CREATE IN nonsense FIELDS (nonsense_a, nonsense_c) VALUES (\"no you were\", \"left behind\")"""
EXAMPLE_DML_LIST__CREATE = [ EXAMPLE0, EXAMPLE1, EXAMPLE2, EXAMPLE3, EXAMPLE4 ]

# DQL examples ('READ')
EXAMPLE5 = """READ IN nonsense ALL RECORDS FIELDS (id, nonsense_a, nonsense_b, nonsense_c)"""
EXAMPLE6 = """READ IN nonsense id 1 FIELDS nonsense_a"""
EXAMPLE7 = """READ IN nonsense id 5 FIELDS nonsense_c"""
EXAMPLE8 = """READ IN nonsense nonsense_b skare FIELDS (id, nonsense_a, nonsense_b, nonsense_c)"""
EXAMPLE9 = """READ IN nonsense nonsense_a \"yeah, right\" FIELDS (nonsense_b, nonsense_c)"""
EXAMPLE_DQL_LIST = [ EXAMPLE5, EXAMPLE6, EXAMPLE7, EXAMPLE8, EXAMPLE9 ]

# DML examples ('UPDATE' and 'DELETE')
EXAMPLE10 = """UPDATE IN nonsense nonsense_b skare FIELDS (nonsense_b) VALUES (scare)"""
EXAMPLE11 = """UPDATE IN nonsense nonsense_b scare FIELDS (nonsense_b) VALUES (skare)"""
EXAMPLE12 = """UPDATE IN nonsense id 1 FIELDS (nonsense_a) VALUES (\"yeah, right\")"""
EXAMPLE13 = """DELETE IN nonsense id 1"""
EXAMPLE14 = """DELETE IN nonsense nonsense_b skare"""
EXAMPLE15 = """UPDATE IN nonsense nonsense_a \"yeah, right\" FIELDS (nonsense_a, nonsense_b, nonsense_c) VALUES (\"hekkin big\", \"skare\", \"today and now\")"""
EXAMPLE_DML_LIST__UPDATE_AND_DELETE = [ EXAMPLE10, EXAMPLE11, EXAMPLE12, EXAMPLE13, EXAMPLE14, \
                     EXAMPLE15 ]

EXAMPLE_LIST = [ EXAMPLE_DML_LIST__CREATE, \
                 EXAMPLE_DQL_LIST, EXAMPLE_DML_LIST__UPDATE_AND_DELETE ]

# end examples delcarations section
# ------------------------------------------------------------------------------
# begin test utility section

# dumps the 'nonsense' table
def dump_nonsense():
    """
    Quickly print what is in the 'nonsense' table.
    """
    return print_2d_list(quick_cindi(EXAMPLE5))

# end test utility section
# ------------------------------------------------------------------------------
# begin test section

# this is the 'unit test'
# if this function returns True, then the system is probably sane.
# if it returns False, then the system needs troubleshooting.
# the only exception which should leak from this function is an AssertionError
# to remind the user about resetting from new all data stores before testing.
def quick_unit_tests():
    """
    Quickly run all the tests in EXAMPLE_LIST to verify CINDI is sane.

    All registered data stores (from config/stores.txt) must have no data,
    but they must have their schema initialized. So for SQL, this means the
    tables have been created, but no inserts have been completed yet.

    Specifically, the stores must be 'new' enough, such that, the primary keys
    which auto-increment would begin at 1. Otherwise, the tests will fail, when
    the primary keys between different stores do not align.

    Please check the CINDI README if there's any confusion on this.
    """
    boolean_result = True

    if not quick_cindi(EXAMPLE5) == [[]]:
        boolean_result = False
        raise AssertionError(\
            "Re-initialize backing stores from new before running examples.")

    i = 0
    test_len = len_2d_list(EXAMPLE_LIST)
    
    try:
        for example_class in EXAMPLE_LIST:
            for example in example_class:
                print("*** Expression test " + str(i) + "\n`" + example + "`\n")
                this_result = quick_cindi(example)
                print_3d_list(this_result)
                i += 1
        # run EXAMPLE5 again, just to be sure
        test_len += 1
        print("*** Expression test " + str(i) + "\n`" + example + "`\n")
        final_example = quick_cindi(EXAMPLE5)
        print_3d_list(final_example)
        i += 1
    except BaseException as err:
        boolean_result = False
        print("Example " + str(i) + " failed: " + str(err))
        traceback.print_exception(*sys.exc_info())
    finally:
        print("\nCompleted " + str(i) + " of " + str(test_len) + " tests.")
        if boolean_result:
            print("*** All tests passed! CINDI is sane! ***")
        else:
            print("!!! Some tests failed! !!!")
    
    return boolean_result

# end test section
# ------------------------------------------------------------------------------
# end of file cindi_tests.py
