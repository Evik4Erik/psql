CREATE DATABASE inventorydb;

CREATE SCHEMA IF NOT EXISTS catalog AUTHORIZATION app_user;

CREATE TABLE catalog.product_categories (
	id serial PRIMARY KEY,
	name TEXT NOT NULL,
	UNIQUE (name)
);

CREATE TABLE catalog.products (
	id serial PRIMARY KEY,
	sku VARCHAR(30) UNIQUE NOT NULL,
	name TEXT NOT NULL,
	price DECIMAL NOT NULL,
	category_id INT REFERENCES catalog.product_categories (id) NOT NULL
);

CREATE TABLE catalog.warehouses (
	id serial PRIMARY KEY,
	city TEXT NOT NULL,
	address TEXT NOT NULL,
	label TEXT,
	is_central BOOLEAN
);

CREATE SCHEMA IF NOT EXISTS sales AUTHORIZATION app_user;

CREATE TABLE sales.orders (
	id serial PRIMARY KEY,
	status TEXT NOT NULL DEFAULT 'unpublished',
	total_amount DECIMAL(10,2) NOT NULL,
	created_at TIMESTAMPTZ NOT NULL,
	warehouse_id INT REFERENCES catalog.warehouses (id) NOT NULL
);

ALTER TABLE sales.orders ADD CONSTRAINT status_constraint CHECK (status in ( 'unpublished', 'new', 'processing', 'pending', 'packing', 'shipped'));

CREATE TABLE sales.order_items (
	price DECIMAL(10,2) NOT NULL,
	quantity INT NOT NULL,
	product_id INT REFERENCES catalog.products (id)  NOT NULL,
	order_id INT REFERENCES sales.orders (id)  NOT NULL,
	PRIMARY KEY (order_id, product_id),
    CONSTRAINT unique_items UNIQUE (order_id, product_id)
);

GRANT ALL ON SCHEMA catalog TO catalog_manager;
GRANT ALL ON SCHEMA sales TO sales_manager;

GRANT All ON ALL TABLES IN SCHEMA catalog to catalog_manager;
GRANT ALL ON ALL TABLES IN SCHEMA sales to sales_manager;

GRANT ALL ON ALL SEQUENCES IN SCHEMA catalog to catalog_manager;
GRANT ALL ON ALL SEQUENCES IN SCHEMA sales TO sales_manager;

GRANT USAGE ON SCHEMA catalog to PUBLIC;
GRANT USAGE ON SCHEMA catalog to sales_manager;

GRANT SELECT ON ALL TABLES IN SCHEMA catalog to PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA catalog to sales_manager;

GRANT SELECT ON ALL SEQUENCES IN SCHEMA catalog to PUBLIC;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA catalog TO sales_manager;

ALTER DEFAULT PRIVILEGES FOR ROLE app_user IN SCHEMA catalog GRANT SELECT ON TABLES TO PUBLIC;