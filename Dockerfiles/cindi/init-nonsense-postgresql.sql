
-- nifty trick from https://stackoverflow.com/a/18389184
SELECT 'CREATE DATABASE db0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'db0')\gexec

\connect db0

create table nonsense (id serial primary key, nonsense_a text, nonsense_b text, nonsense_c text);
