ALTER TABLE auth.users ADD COLUMN warehouse_id INT REFERENCES catalog.warehouses (id);

CREATE OR REPLACE VIEW ship_delivery AS 
SELECT id, status, warehouse_id FROM sales.orders;
