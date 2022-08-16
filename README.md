# Cacheable Implementation Neutral Data Intermediate
*CINDI* is a *Meta Database Management System* which provides a simple way for
front-end applications to perform [*CRUD*](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) operations  with various back-end
stores.  *CINDI* is written in *Python 3*, and is available in the [*PyPI Index* as a *PIP* package](https://pypi.org/project/cindi/).  

*CINDI* is a service to translate *INDI* language statements to either *SQL*, *MongoDB*, or *Redis*.  *CINDI* also caches read queries in memory, so that clients asking for the same thing repetitively do not actually get to hit the backing-stores.

*CINDI* is intended to be used during the early rapid-prototyping / idea phase, so that developers may focus on the layout, functionality, and usability of a front-end application.  **Think of *CINDI* as a temporary substitute**, until a proper back-end infrastructure is built.  This way, the initial pioneers of a project need only to focus their energy on the front-end(s).

The idea is to forgo the traditional map of API endpoints usually provided by a back-end.  Instead, front-end code will submit *INDI* statements directly to a single endpoint, and receive *JSON* responses accordingly. The result is, most application logic is shifted into the front-end code, which simplifies the rapid prototyping of applications.

Later, when a minimal-viable-product had been demonstrated to stakeholders, and more developers can be assigned to the project, *CINDI* would then be replaced with a traditional API back-end.

Users may configure *CINDI* to use one, some, or all of the currently supported storage systems:

- PostgreSQL
- MySQL
- SQLite3
- MongoDB
- Redis

An easy *Implementation Neutral Data Intermediate* language is provided in order to abstract-away the underlying chosen store(s).  The *INDI* language is similar to *SQL*, but re-worded to enforce the *CRUD* mentality.

## Brief INDI Language Tutorial
The *INDI* language uses four major *CRUD* keywords: `CREATE`, `READ`, `UPDATE`, and `DELETE`. 

*CINDI* will **cache** `READ` operations in-memory, until it detects those result-sets are stale (due to another `CREATE`, `UPDATE`, or `DELETE` affecting the data).

In order to demonstrate the *INDI* language, consider the following *SQLite3* schema:

	 CREATE TABLE nonsense (
	 	id INTEGER NOT NULL PRIMARY KEY,
		nonsense_a TEXT,
		nonsense_b TEXT,
		nonsense_c TEXT
		);

The above *SQL* statement would be prepared (manually, by the user) for *CINDI* before starting. Then, after loading *CINDI*, the four *CRUD* operations may be performed by submitting *INDI* statements to the system.

For example, here is an *INDI* `CREATE` statement:

    CREATE IN nonsense FIELDS (nonsense_a, nonsense_b, nonsense_c) VALUES ("hekkin big", "skare", "today and now")

There would be no 'result' to the above query, other than the underlying store(s) being modified to reflect the insertion of new data.  Client-side, this is what would be received as a response:

    [[]]

Next example, here is an *INDI* `READ` statement:

    READ IN nonsense id 1 FIELDS nonsense_a

The `READ` has a result, it would be a JSON array looking like this:

    [[['hekkin big']]]

Now for a more comprehensive `READ`:

    READ IN nonsense ALL RECORDS FIELDS (id, nonsense_a, nonsense_b, nonsense_c)

This retrieves all records from the nonsense table, including all columns:

    [[[1, 'hekkin big', 'skare', 'today and now']]]

It appears that 'skare' is spelled wrong, so to `UPDATE` that:

    UPDATE IN nonsense nonsense_b skare FIELDS (nonsense_b) VALUES (scare)

The literal result is an empty set:

    [[]]

Check to see just that column had been updated:

    READ IN nonsense id 1 FIELDS nonsense_b

Result:

    [[['scare']]]

Finally, to `DELETE` the record:

    DELETE IN nonsense id 1

A subsequent `READ` would return an empty set.  Note the `DELETE` may have queried by any field, not just the 'id'!

`VALUES` quotes are optional, unless the string to be stored contains spaces.

**See the [`doc/demo.txt`](https://github.com/ultasun/cindi/blob/master/doc/demo.txt) file for the verbose output from the above demo.**

The `doc` folder also contains schema examples for the other supported systems.

### Why ?

The above demonstration may seem trivial, however, consider that *CINDI* will support managing these *INDI* statements even if the backing-store is a *NoSQL* solution, such as *MongoDB* or *Redis*.  The results are consistent, and if multiple stores are enabled, then any cache-missed `READ` will query all the stores, and compare the results to ensure consistency across the storage mechanisms.

If clients are submitting the same *INDI* queries repetitively, then the result from the first time is served from an in-memory *Python dictionary*.  That cached query is discarded when an affecting `CREATE`, `UPDATE`, or `DELETE` occurs.

In the case of the *NoSQL* solutions, *CINDI* manages the concept of tables, columns, and primary keys.  In particular, the *MongoDB* setup requires only creating a database, and the *Redis* setup requires nothing!

**CINDI will not automatically initialize SQL / Mongo schemas**, this must be done manually prior to runtime. That is why the author has provided a couple *Docker* demos, read on!

**Check [`cindi_tests.py`](https://github.com/ultasun/cindi/blob/master/src/cindi/cindi_tests.py) for more *INDI* language examples.**

## Installation, Easiest: *cindi-lite* Docker Compose Pack
[Please go here](https://github.com/ultasun/cindi-lite) and follow the instructions in order to have *Docker Compose* orchestrate the setup of [`ultasun/cindi-lite`](https://hub.docker.com/r/ultasun/cindi-lite), which will consume the least resources. Along the way, you'll learn everything there is to know about configuring the *CINDI* runtime for a **minimalist *SQLite3*-only backing-store.**
## Installation, Easier: *cindi-plus* Docker Compose Pack
[Please go here](https://github.com/ultasun/cindi-plus) and follow the instructions in order to have *Docker Compose* orchestrate the complete setup and demonstration of [`ultasun/cindi`](https://hub.docker.com/r/ultasun/cindi), which will, by default, consume significantly more resources than [`ultasun/cindi-lite`](https://hub.docker.com/r/ultasun/cindi-lite). Along the way, you'll learn everything there is to know about configuring the *CINDI* runtime for a **full installation with all five supported backing-stores running simultaneously**

## Installation, Easy: *cindi-lite* Docker image (no orchestration)
A *Docker* image [`ultasun/cindi-lite`](https://hub.docker.com/r/ultasun/cindi-lite) is available on *Docker Hub*, it will use a *SQLite3* setup, and provide a similar experience to *Installing & Basic Setup on SQLite3*.

After start-up, development *Flask* server will **not** have *SSL* enabled.

0. Install the latest version of *Docker* on your system.
1. Open a terminal, and run the following command for a disposable demo:
   - `$ docker run -dp 36963:36963 --rm ultasun/cindi-lite`
   - Or, if you'd like to persist logs and data with *named-mounts*:
   - `$ docker run -dp 36963:36963 -v cindi-lite-data:/app/data -v cindi-lite-logs:/app/logs ultasun/cindi-lite`
   - Feel free to use *bind-mounts* for easier access to the produced data.
2. Use *Docker Desktop* to open a terminal into the running container, or otherwise `docker exec -it` into the container, and initialize the **EXAMPLE** data:
   - `$ python`
   - `>>> import cindi`
   - `>>> cindi.quick_unit_tests()`
   - Verify the return value is `True`, which means all 17 tests passed!
3. Use *Postman* (or something) to *POST* some *INDI* statements to `http://localhost:36963/evaluate`, such as:
   - `READ IN nonsense ALL RECORDS FIELDS (id, nonsense_a, nonsense_b, nonsense_c)`
   - Back in the *python* console, the full list of **EXAMPLES** may be viewed:
   - `>>> cindi.print_2d_list(cindi.EXAMPLE_LIST)`
     - These are the **EXAMPLES** which were ran during `cindi.quick_unit_tests()`
       - There is no harm in running the *DDL* or *DML* statements again!


## Hard: Manual Installation & Basic Setup on SQLite3
### *Installing without Docker*
**Docker is not necessary to utilize *CINDI***.  This installation demo will show manual installation from PyPI, and configuration using only *SQLite3*, to keep it brief.  Please follow the detailed tutorial on [`cindi-plus`](https://github.com/ultasun/cindi-plus) to learn about configuring other backing-store systems.

1. `pip install cindi`
2. In your current working directory, create a folder called `config`:
   - `$ mkdir config`
3. In the `config` folder, create empty `stores.txt` and `tables.txt` files.
   - `$ cd config && touch stores.txt && touch tables.txt && cd ..`
4. Open `stores.txt` with a text editor -- the file must contain a python dictionary, here is the basic example using only *SQLite3*:
   - `{'sqlite3': {'db': 'db0', 'sqlite3_file_prefix': ''}}`
5. Open `tables.txt` with a text editor -- the file must contain a python list (or tuple), here is the basic example:
   - `['nonsense']`
6. To open the *SQLite3* database for intialization, in your terminal, run:
   - `$ sqlite3 db0.db`
   - You may need to install *SQLite3* if the command is not found.
7. In the *SQLite3* console, initialize the schema:
   - `sqlite> CREATE TABLE nonsense (id INTEGER NOT NULL PRIMARY KEY, nonsense_a TEXT, nonsense_b TEXT, nonsense_c TEXT);`
   - Save and quit: `sqlite> .quit`
8. In your terminal, run:
   - `$ python3`
9. Finally, try it out!  Populate the store(s) with **EXAMPLE** data:
   - `>>> import cindi`
   - `>>> cindi.quick_unit_tests()`
        - The above function returns `True` if all tests succeed.
   - `>>> cindi.quick_cindi(cindi.EXAMPLE5)`
        - The above function returns a multi-dimensional list of values.
---
## Logging
Since *CINDI* is in the alpha development stage, every *DML* statement is logged in the `logs/` directory. Whatever data you're submitting, a copy will be saved in that directory.
- This will consume disk space.
- This will expose sensitive data.

There is one *INDI* *DML* statement per file. Each filename ends with a nano-seconds-since-epoch timestamp. A filename prefixed with `indi` is a *DML* expression. At the time of this writing, there are no other files written to the `logs/` directory.

There is no simple way to disable this disk logging without modifying the source code. Just re-define `def fprint(w, x='', y='', z=''):` to do nothing if you must. *CINDI* is in the alpha development stage, and it is designed to assist in developing apps which are also in the alpha development stage. *SSL* on the *Flask* development server is not even enabled, and the development server is 'not for production use' anyway.

## Troubleshooting
*CINDI* is in the alpha development stage. If you've encountered a problem, then you've probably found a bug in the translation routines, or your backing-stores are not configured correctly.

*CINDI* will generally exit the *Python3* process on most errors ('fail fast'). The `logs/` directory is ordred by nanoseconds-since-epoch timestamps, so it should be easy to work-backwards to locate the *INDI* *DML* statement which was translated inconsistently across multiple backing-stores. The author can't forsee any other reason for *CINDI* to crash, besides a backing-store connectivity issue.

When the *Python3* process exits, various [exit codes](https://mariadb.com/kb/en/operating-system-error-codes/) are used. This helps frequent users/developers of *CINDI* quickly identify from the *Docker* console (or elsewhere) why an `exit` had occurred.

Here are the exit numbers and error messages which might be produced by *CINDI*:
- **117**: `Corrupted store, please file a bug. Check the CINDI README.`
  - The chain of *INDI* *DML* statements which were submitted to CINDI for execution over time, had managed to cause different **inconsistent** results to appear in the various backing stores.
  - This will crash the system because, every *DQL* statement executed verifies consistency across all conneected backing stores ('fail fast'). So *CINDI* had a translation error during an earlier *DML* statement.
  - **Remedy Options**:
    - **First,** please submit a bug with the full contents of `logs/`, and santize your data first if possible. This error is really not the fault of the user (you). The `VALUES` may not be so important, so a simple script to truncate after the `VALUES` in each file within the `logs/` directory if you can't or won't share the `VALUES`.
      - However, the `VALUES` would be appreciated, because **some parts of the translation code might do the wrong action if a value has too many single-or-double-quotes**, it's a your-milage-may-vary scenario (at this time).
      	- Regular expressions might be used in the future to mitigate some of the forseen issues regarding single-and-double quotes
	  - Because a proper recursive solution might be needed.
    - **Second,** either:
      - Manually adjust the backing-stores, using their native tools/clients, until the data is consistent.
      	- Success will be obvious when *DQL* statements regarding the 'offending table' no longer cause *CINDI* to exit.
      - Wipe all backing stores, and reload all the *INDI* statements from new.
- **5**: `fprint failed to print to file: ...`
  - The log-to-disk mechanism `fprint` failed to write a file.
  - **Remedy Options**:
    - Disk space full?
    - Lost directory permissions during runtime?
- **52**: `!! ERROR: The quantity of fields detected is not euqal to the number of values detected...`
  - The submitted *INDI* *DML* statement does not have the same quantity of `FIELDS` and `VALUES`, **or**,
  - The submitted *INDI* *DML* statement was unable to be parsed properly by the translation routine.
    - Please submit a bug containing the *INDI* *DML* statement which caused this.
      - Submitting the full `logs/` should not be necessary, because this error would be isolated to parsing a specific *INDI* *DML* statement before any writing to a backing-store occured.
  - **Remedy Options**:
    - Check the *INDI* syntax
    - Manipulate the single-quotes or double-quotes in the `VALUES` of the offending statement
      - Many nested single-quotes or double-quotes might confuse the translation routine.
      	- Remove the quotes, and please submit a bug.
	- Regular expressions will probably be used in the future to avoid problems like this.
- **29**: `Redis SET failed.`
  - While performing a *Redis* `SET`, it failed.
  - **Remedy Options**:
    - Was *CINDI* disconnected from *Redis* in the middle of the transaction?
    - Did *CINDI* lose write access to the *Redis* database for some reason?
  - Please submit a bug in any event! Thank you.
- **2**: Relating to a configuration 'File Not Found':
  - `config/stores.txt not found, please check the CINDI README.`
  - `config/tables.txt not found, please check the CINDI README.`
  - **Remedy Options**:
    - The `config/` directory must be in the same directory `.` as where the *Python3* process was launched. This is an elementary user mistake. Please review this README file carefully, or check one of the published *Docker* images for a proper example of how the *Python3* process needs to be launched.
    - The `config/stores.txt` or `config/tables.txt` files are missing or not named properly.
- **61**: Relating to a configuration file 'Invalid Syntax':
  - `config/stores.txt not a dictionary, check the CINDI README.`
    - **Remedy Option**
      - `config/stores.txt` must be a [*Python3* *dictionary*](https://docs.python.org/3/tutorial/datastructures.html#dictionaries). Check the syntax of what is in the file, and try again.
  - `config/tables.txt must be a list or tuple, check CINDI README.`
    - **Remedy Option**
      - `config/tables.txt` must be a [*Python3* *list* or *tuple*](https://docs.python.org/3/tutorial/introduction.html#lists). Check the syntax of what is in the file, and try again.
  - `No stores defined in config/stores.txt! Check CINDI README.`
    - **Remedy Option**
      - The `config/stores.txt` file has an empty dictionary in it.
      	- Review this README file carefully, you must define at least one backing-store for *CINDI* to use!
- **49**: `Failed to initialize XXXXX connection.`
  - *Python3* support for your chosen backing-store mechanism is not installed, **or**,
  - The connection/credential to the backing store is bad, **or**, the database you had specified to connect to in `config/stores.txt` is not available.
  - **Remedy Option**
    - Verify the *Python3* client library for the specified backing-store is installed.
    - Verify the credentials to the backing-store are valid and specified correctly in `config/stores.txt`
    - Verify the database configured in `config/stores.txt` exists, permissions are good, and so on.
    - `...sqlite3 connection, file not found?`
      - Perhaps the database file was deleted, or access was lost.
      	- *CINDI* will not automatically re-create the *SQLite3* database in this event.
	- Either reconstruct the *SQLite3* database manually, **or**,
	- Wipe out all backing-stores, and start again from new.
  - **Submit a bug if continuing to have difficulty connecting to a store, perhaps something changed in an underlying connectivity library!**
- **131**: `High level error: ...`
  - Some error, likely in a driver, occured.
  - **Remedy Option: If the solution is not obvious, then you should submit a bug.**
    - Especially if the problem is an *OperationalError*, complaining the *SQL* syntax is invalid.
- **22**: `Low level error: ...`
  - Some error, unforseen by the author, occured.
  - **Remedy Option: If the solution is not obvious, then you should submit a bug.**

### Cache Duality Caveat
**If you have multiple *CINDI* instances running against the same backing-stores, then a cache in one instance will not have a way to know if a *DML* `CREATE`/`UPDATE`/`DELETE` occured in another instance.**  Please do not allow multiple clones of *CINDI* to interact with the same backing-stores concurrently.
- A simple solution to this in a future release will be to have a `/cache-clear` endpoint in *Flask*, **or**
- A file on the file system is monitored, if it is changed, then other instances know to clear the cache.

See the next section regarding **Support**!

## Support
The author is available for questions, comments and criticism in #cindi on [Libera.Chat](https://libera.chat).

## Credits
Please read the [LICENSE](https://github.com/ultasun/cindi/blob/master/LICENSE).  This software was written by a single individual.  This is alpha-quality software, you are likely to find bugs!  Please submit feedback!
**Thank you for evaluating *CINDI*!**

