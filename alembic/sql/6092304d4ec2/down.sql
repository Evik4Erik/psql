REVOKE USAGE ON SCHEMA inventory FROM worker;
REVOKE SELECT, UPDATE ON ALL TABLES IN SCHEMA inventory FROM worker;

DROP TABLE IF EXISTS  inventory.delivery_items;
DROP TABLE IF EXISTS  inventory.transfer_items;
DROP TABLE IF EXISTS  inventory.transfers; 
DROP TABLE IF EXISTS  inventory.deliveries;

DROP TABLE IF EXISTS  inventory.stock;
DROP TABLE IF EXISTS  inventory.routes;

REVOKE ALL ON SCHEMA inventory FROM inventory_manager;
REVOKE All ON ALL TABLES IN SCHEMA inventory FROM inventory_manager;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA inventory FROM inventory_manager;

REVOKE USAGE ON SCHEMA catalog FROM inventory_manager;

DROP SCHEMA IF EXISTS inventory;

ALTER TABLE catalog.warehouses ALTER COLUMN city TYPE TEXT USING city::text;

REVOKE All PRIVILEGES ON TABLE catalog.cities FROM catalog_manager;
REVOKE SELECT ON TABLE catalog.cities  FROM sales_manager;

DROP TABLE IF EXISTS  catalog.cities;
