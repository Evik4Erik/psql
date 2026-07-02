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

ALTER TABLE catalog.warehouses ADD COLUMN city_id INT;

UPDATE catalog.warehouses
SET city_id = 
    CASE 
        WHEN city = 'Москва'            THEN 1
        WHEN city = 'Санкт-Петербург'   THEN 2
        WHEN city = 'Новосибирск'       THEN 3
        WHEN city = 'Екатеринбург'      THEN 4
        WHEN city = 'Казань'            THEN 5
        WHEN city = 'Нижний Новгород'   THEN 6
        WHEN city = 'Челябинск'         THEN 7
        WHEN city = 'Самара'            THEN 8
        WHEN city = 'Омск'              THEN 9
        WHEN city = 'Ростов-на-Дону'    THEN 10
        WHEN city = 'Уфа'               THEN 11
        WHEN city = 'Красноярск'        THEN 12
        WHEN city = 'Воронеж'           THEN 13
        WHEN city = 'Пермь'             THEN 14
        WHEN city = 'Волгоград'         THEN 15
        ELSE 1
    END;


ALTER TABLE catalog.warehouses DROP COLUMN city;

CREATE SCHEMA IF NOT EXISTS inventory;

ALTER DEFAULT PRIVILEGES FOR ROLE app_user IN SCHEMA inventory GRANT ALL ON TABLES TO inventory_manager;
ALTER DEFAULT PRIVILEGES FOR ROLE app_user IN SCHEMA inventory GRANT ALL ON SEQUENCES TO inventory_manager;
GRANT SELECT, UPDATE ON sales.orders to inventory_manager;

CREATE TABLE IF NOT EXISTS inventory.routes (
	from_city_id INT NOT NULL REFERENCES catalog.cities (id) NOT NULL,
	to_city_id INT NOT NULL REFERENCES catalog.cities (id) NOT NULL,
    duration TIME NOT NULL, 
    total_threshold DECIMAL NOT NULL,
    PRIMARY KEY (from_city_id, to_city_id)
);

CREATE TABLE IF NOT EXISTS inventory.stocks (
    warehouse_id INT REFERENCES catalog.warehouses (id) NOT NULL,
    product_id INT REFERENCES catalog.products (id) NOT NULL,
    quantity INT,
    PRIMARY KEY (warehouse_id, product_id)
);

CREATE TABLE IF NOT EXISTS inventory.reserves (
	id serial PRIMARY KEY,
    order_id INT REFERENCES sales.orders (id) NOT NULL,
    product_id INT REFERENCES catalog.products (id) NOT NULL,
    warehouse_id INT REFERENCES catalog.warehouses (id) NOT NULL,
    quantity INT,
    CONSTRAINT unique_reserves UNIQUE (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS inventory.deliveries (
    order_id INT REFERENCES sales.orders (id) NOT NULL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipping', 'shipped')),
    updated_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS  inventory.delivery_items (
    order_id INT REFERENCES inventory.deliveries (order_id) NOT NULL,
    product_id INT REFERENCES catalog.products (id) NOT NULL,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipped')),
    updated_at TIMESTAMPTZ,
    PRIMARY KEY (order_id, product_id)
);
CREATE TABLE IF NOT EXISTS  inventory.transfers (
    id SERIAL PRIMARY KEY,
    from_warehouse_id INT REFERENCES catalog.warehouses (id) NOT NULL,
    to_warehouse_id INT REFERENCES catalog.warehouses (id) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipping', 'in_transit', 'arrived', 'received')),
    updated_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    arriving_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ -- можно сделать ограничение, чтоб времна были последовательны
);
CREATE TABLE IF NOT EXISTS  inventory.transfer_items (
    id serial PRIMARY KEY,
    transfer_id INT REFERENCES inventory.transfers (id) NOT NULL,
    product_id INT REFERENCES catalog.products (id) NOT NULL,
    status TEXT NOT NULL CHECK ( status IN ('planned', 'shipped', 'received')),
    quantity INT NOT NULL,
    updated_at TIMESTAMPTZ,
    requested_by INT REFERENCES auth.users (id) NOT NULL,
    reserve_id INT REFERENCES inventory.reserves (id)
);

GRANT USAGE ON SCHEMA inventory to worker;
GRANT ALL ON inventory.stocks to worker;
GRANT SELECT, UPDATE ON inventory.reserves to worker;
GRANT SELECT, UPDATE (status, updated_at) ON inventory.deliveries to worker;
GRANT SELECT, UPDATE (status, updated_at) ON inventory.delivery_items to worker;
GRANT SELECT, UPDATE (status, updated_at) ON inventory.transfers to worker;
GRANT SELECT, UPDATE (status, updated_at) ON inventory.transfer_items to worker;
GRANT SELECT ON ALL TABLES IN SCHEMA inventory to worker;
