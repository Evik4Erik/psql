GRANT ALL ON SCHEMA catalog TO catalog_manager;
GRANT ALL ON SCHEMA sales TO sales_manager;

GRANT SELECT ON ALL SEQUENCES IN SCHEMA catalog to PUBLIC;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA catalog TO sales_manager;

ALTER DEFAULT PRIVILEGES FOR ROLE catalog_manager IN SCHEMA catalog GRANT SELECT ON TABLES TO PUBLIC;

CREATE SCHEMA auth;
CREATE TABLE auth.users(
	id SERIAL PRIMARY KEY,
	username TEXT UNIQUE NOT NULL,
	password TEXT NOT NULL,
	role TEXT NOT NULL
);

GRANT USAGE ON SCHEMA auth TO PUBLIC;
GRANT SELECT ON TABLE auth.users to PUBLIC;

insert into auth.users (username, password, role) VALUES ('cat_man', crypt('pass', gen_salt('bf')), 'catalog_manager');

ALTER TABLE sales.orders ADD COLUMN created_by INT NOT NULL DEFAULT '1';
ALTER TABLE sales.orders ADD CONSTRAINT created_by_user FOREIGN KEY (created_by) REFERENCES auth.users (id);
