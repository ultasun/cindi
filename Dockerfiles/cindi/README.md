# Docker Compose Pack for *cindi-plus*
[*CINDI*](https://github.com/ultasun/cindi) is a *Meta Database Management System* which provides a simple way for front-end applications to perform [*CRUD*](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) operations  with various back-end stores.  *CINDI* is written in *Python 3*, and is available in the [*PyPI Index* as a *PIP* package](https://pypi.org/project/cindi/).

This git repository makes available a *docker compose pack* in order for end users to get running with *CINDI* quickly, to enable the tenet of supporting rapid application prototyping.

This *docker compose pack* utilizes several *Docker* images, but the spot-light image is called [*cindi*](https://hub.docker/com/repository/docker/ultasun/cindi). In total, there are five images, so *docker compose* is used to orchestrate the setup.

***MySQL*, *PostgreSQL*, *SQLite3*, *MongoDB*, and *Redis* will all be available as backing-store options** -- you may configure to use all, some, or just one.

*cindi-plus* uses significantly more resources (and electricity) than a slimmer CINDI outfit.  **If you would prefer to use the slim outfit, then use the [*cindi-lite*](https://github.com/ultasun/cindi-lite) pack instead.**

## Setup
The following instructions assume a *UNIX*-like system.
1. Install [*Docker*](https://www.docker.com) for your system.
2. Clone this *git* repository, open a terminal and run:
   - `$ git clone https://github.com/ultasun/cindi-plus`
      - **Or, if you do not have *git* installed**, download the ZIP archive from this page, extract the ZIP archive, and `cd` your *Terminal* or *Console* into the directory created by extracting the archive.
3. *cindi-plus* supports several [*Database Management Systems*](https://en.wikipedia.org/wiki/Database#Database_management_system), and you can see that configuration in [`config/stores.txt`](https://github.com/ultasun/cindi-plus/blob/master/config/stores.txt). It is a *Python dictionary*.
   - **Please view [`config/stores.txt`](https://github.com/ultasun/cindi-plus/blob/master/config/stores.txt) before continuing.**
      - The `'db'` key is used in all five *DBMS* clients, and while the example shows all five being identical, it is not a technical necessity -- the value may be different in each backing-store.
      - The remaining keys are hopefully self-documenting, except for a little ambiguity in the `'redis'` section:
	      - Since *Redis*' definition of a *database* is one of sixteen slots, the `['redis']['redisDb']` key indicates the integer value of which one you would like to use.
	      - So, `['redis']['db']` indicates the *redis key prefix* as *CINDI* does *Redis* `SET`'s during [*DML*](https://en.wikipedia.org/wiki/Data_manipulation_language)-type [*INDI*](https://github.com/ultasun/cindi) statements.
4. *CINDI* does not automatically generate *SQL* [*DDL*](https://en.wikipedia.org/wiki/Data_definition_language) statements, nor does it automatically configure *MongoDB*'s database credentials. You must do this yourself, and altering the schemas after the first start-up has not been tested.
   - **Symmetry must be maintained among all enabled backing-stores which require *DDL* initialization!**
	   - This means the semantic meaning of all `*.sql` files *must be equivalent*, despite the semantic differences between *SQL* implementations.
		   - Otherwise, ***CINDI* will crash when inconsistencies between backing-stores are detected.**
   - Please take the time now, to read the following four files, regarding example *DDL* configuration: 
	   - [`init-nonsense-sqlite3.sql`](https://github.com/ultasun/cindi-plus/blob/master/init-nonsense-sqlite3.sql)
	   - [`init-nonsense-mysql.sql`](https://github.com/ultasun/cindi-plus/blob/master/init-nonsense-mysql.sql)
	   - [`init-nonsense-postgresql.sql`](https://github.com/ultasun/cindi-plus/blob/master/init-nonsense-postgresql.sql)
	   - [`init-nonsense-mongodb.js`](https://github.com/ultasun/cindi-plus/blob/master/init-nonsense-mongodb.js)
		   - Strictly speaking, `init-nonsense-mongodb.js` might not be regarded as *DDL*, but the larger purpose of *Step 4* is to cover backing-store initialization.
		   - *MongoDB* configuration needs a username associated with the database referenced in `['mongodb']['db']` within `config/stores.txt`, which, inherently,
		   - Requires the creation of a *MongoDB* database,
			   - Which in this case, is called `db0`.   
	   - **There is no `init-nonsense-redis.?`, because the *Redis* instance requires zero configuration.**
   - When composing *DDL* intended for *CINDI* registration in each `*.sql` initialization file, **there are some restrictions**, which are:
     - Each table intended for *CINDI* registration **must** have an auto-incrementing primary key column called `id`.
     - No foreign key constraints for tables intended for *CINDI* registration.
     - Every other column in a table intended for *CINDI* registration **must** be a string data type, such as `TEXT` in the case of *SQLite3*, `LONGTEXT` in the case of *MySQL*, and so on.
       - Clients are likely receiving *JSON* objects via *CINDI*'s *HTTP Flask* service, so this should not pose any practical limitations regarding the handling of floating point numbers, booleans, etc.
	       - If this is regarded as a serious limitation for your application, then *CINDI* might not fit your use-case, and you should invest the time now to develop a proper back-end API.
   - There may be 'background tables', procedures, triggers, constraints, and other features utilized in the backing-store.
     - These 'background components' must **not** be registered with *CINDI* in `config/tables.txt`.
     - These 'background components' might be okay to manipulate the *CINDI*-aware tables.
       - [*ACID*](https://en.wikipedia.org/wiki/ACID) violations leading to corruption may occur, if serving multiple users, or if your 'background features' become too elaborate.
       	 - This would be a scenario when you should begin considering life after *CINDI*.
    - **As the *Docker* container starts the first time, your defined** (or the default '*nonsense*') **initialization scripts** (the three `*.sql` files) **will be executed against its respective store.** 
	     - The *MongoDB* `*.js` file will be processed at this time, too.
	     - Again, Redis requires zero configuration.
5. *CINDI* does not automatically detect what is in any backing-store, you must register which tables are *CINDI* tables in `config/tables.txt`.
   - This is how the database may have extra 'background' features; such as tables, procedures, triggers, constraints between these non-registered objects, etc.
	   - In other words, *CINDI* ignores tables which have not been registered in `config/tables.txt`.
   - `config/tables.txt` *MUST* be a *Python list* (or *tuple*), for example:
	    - `["nonsense"]`
   - ***CINDI* will only manage the tables specified in this *list*.**
6. That's it! In your terminal window, `cd` into the directory with the `docker-compose.yml` file, and run
   - `$ docker compose up`

**If you started *CINDI* with the default schema**, then, `docker exec -it` your way into the container (or, if using *Docker Desktop*, click on the little terminal icon in the container list), and run the following commands to get some action:
   - `$ python`
   - `>>> import cindi`
      - You should see confirmations that all four connectivity drivers were loaded.
      - *SQLite3* is always available, so there will not be a confirmation/deny message.
   - `>>> cindi.quick_unit_tests()`
     - This runs all of the [*INDI*](https://github.com/ultasun/cindi) expressions in `cindi.EXAMPLE_LIST`
     - You may pretty-print these using:
       - `>>> cindi.print_2d_list(cindi.EXAMPLE_LIST)`
   - `>>> print(cindi.EXAMPLE5)`
   - `>>> cindi.quick_cindi(cindi.EXAMPLE5)`

## More on *CINDI*
Check the full [*CINDI* README](https://github.com/ultasun/cindi) if you'd like more ideas of what to do next,  or why *CINDI* is helpful for supporting the rapid prototyping of web applications.

Thank you for reading and utilizing *CINDI*!
