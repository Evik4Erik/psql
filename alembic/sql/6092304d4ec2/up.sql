CREATE TABLE IF NOT EXISTS  catalog.cities(
	id SERIAL PRIMARY KEY,
	city TEXT UNIQUE NOT NULL
);

INSERT INTO catalog.cities (city) VALUES 
    ('Москва'),
    ('Санкт-Петербург'),
    ('Новосибирск'),
    ('Екатеринбург'),
    ('Казань'),
    ('Нижний Новгород'),
    ('Челябинск'),
    ('Самара'),
    ('Омск'),
    ('Ростов-на-Дону'),
    ('Уфа'),
    ('Красноярск'),
    ('Воронеж'),
    ('Пермь'),
    ('Волгоград');

GRANT All PRIVILEGES ON TABLE catalog.cities to catalog_manager;
GRANT SELECT ON TABLE catalog.cities to sales_manager;

ALTER TABLE catalog.warehouses ALTER COLUMN city TYPE INT USING city::integer;

CREATE SCHEMA IF NOT EXISTS inventory;

GRANT ALL ON SCHEMA inventory TO inventory_manager;
GRANT All ON ALL TABLES IN SCHEMA inventory to inventory_manager;
GRANT ALL ON ALL SEQUENCES IN SCHEMA inventory to inventory_manager;

GRANT ALL ON SCHEMA inventory TO app_user;
GRANT All ON ALL TABLES IN SCHEMA inventory to app_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA inventory to app_user;

GRANT USAGE ON SCHEMA catalog to inventory_manager;
--GRANT SELECT ON ALL TABLES IN SCHEMA catalog to inventory_manager;

SET ROLE app_user;

CREATE TABLE IF NOT EXISTS inventory.routes (
	id serial PRIMARY KEY,
	from_ INT NOT NULL REFERENCES catalog.warehouses (id) NOT NULL,
	to_ INT NOT NULL REFERENCES catalog.warehouses (id) NOT NULL,
    duration INT NOT NULL, 
    total_threshold DECIMAL NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory.stock (
	id serial PRIMARY KEY,
    warehouse_id INT REFERENCES catalog.warehouses (id) NOT NULL,
    product_id INT REFERENCES catalog.products (id) NOT NULL,
    quantity INT,
    CONSTRAINT unique_stocks UNIQUE (warehouse_id, product_id)
);

CREATE TABLE IF NOT EXISTS inventory.reserves (
	id serial PRIMARY KEY,
    order_id INT REFERENCES sales.orders (id) NOT NULL,
    product_id INT REFERENCES catalog.products (id) NOT NULL,
    quantity INT,
    CONSTRAINT unique_reserves UNIQUE (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS inventory.deliveries (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipping', 'shipped')),
    shipped_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS  inventory.delivery_items (
    id serial PRIMARY KEY,
    order_id INT NOT NULL REFERENCES sales.orders (id) NOT NULL,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipped'))
);
CREATE TABLE IF NOT EXISTS  inventory.transfers (
    id serial PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipping', 'in_transit', 'arrived', 'received')),
    started_at TIMESTAMPTZ,
    arriving_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ -- можно сделать ограничение, чтоб времна были последовательны
);
CREATE TABLE IF NOT EXISTS  inventory.transfer_items (
    id serial PRIMARY KEY,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipped', 'received'))
);

RESET ROLE;

GRANT USAGE ON SCHEMA inventory to worker;
GRANT SELECT, UPDATE ON ALL TABLES IN SCHEMA inventory to worker;

insert into auth.users (username, password, role) VALUES ('worker', crypt('pass', gen_salt('bf')), 'worker');
insert into auth.users (username, password, role) VALUES ('inv', crypt('pass', gen_salt('bf')), 'inventory_manager');
