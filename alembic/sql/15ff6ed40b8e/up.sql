SET ROLE app_user;

CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE IF NOT EXISTS  auth.users(
	id SERIAL PRIMARY KEY,
	username TEXT UNIQUE NOT NULL,
	password TEXT NOT NULL,
	role TEXT NOT NULL
);

GRANT USAGE ON SCHEMA auth TO PUBLIC;
GRANT SELECT ON TABLE auth.users to PUBLIC;

insert into auth.users (username, password, role) VALUES ('cat_man', crypt('pass', gen_salt('bf')), 'catalog_manager');

ALTER TABLE sales.orders ADD COLUMN IF NOT EXISTS created_by INT NOT NULL DEFAULT '1';

ALTER TABLE sales.orders DROP CONSTRAINT IF EXISTS created_by_user;
ALTER TABLE sales.orders ADD CONSTRAINT created_by_user FOREIGN KEY (created_by) REFERENCES auth.users (id);

RESET ROLE;