# Cacheable Implementation Neutral Data Intermediate
*CINDI* is a *Meta Database Management System* which provides a simple way for
front-end applications to perform [*CRUD*](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) operations  with various back-end
stores.  *CINDI* is written in *Python 3*, and is available in the [*PyPI Index* as a *PIP* package](https://pypi.org/project/cindi/).  

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

---

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

## Support
The author is available for questions, comments and criticism in #cindi on [Libera.Chat](https://libera.chat).

## Credits
Please read the [LICENSE](https://github.com/ultasun/cindi/blob/master/LICENSE).  This is alpha-quality software, you are likely to find bugs!  Please submit feedback!
**Thank you for evaluating *CINDI*!**

