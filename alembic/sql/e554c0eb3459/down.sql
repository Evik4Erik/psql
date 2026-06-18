ALTER DEFAULT PRIVILEGES FOR ROLE catalog_manager IN SCHEMA catalog GRANT SELECT ON TABLES TO PUBLIC;

REVOKE SELECT ON ALL SEQUENCES IN SCHEMA catalog FROM PUBLIC;
REVOKE SELECT ON ALL SEQUENCES IN SCHEMA catalog FROM sales_manager;

REVOKE All ON ALL TABLES IN SCHEMA catalog FROM catalog_manager;
REVOKE ALL ON ALL TABLES IN SCHEMA sales FROM sales_manager;

REVOKE ALL ON ALL SEQUENCES IN SCHEMA catalog FROM catalog_manager;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA sales FROM sales_manager;

REVOKE USAGE ON SCHEMA catalog FROM PUBLIC;
REVOKE USAGE ON SCHEMA catalog FROM sales_manager;

REVOKE SELECT ON ALL TABLES IN SCHEMA catalog FROM PUBLIC;
REVOKE SELECT ON ALL TABLES IN SCHEMA catalog FROM sales_manager;

REVOKE ALL ON SCHEMA catalog FROM catalog_manager;
REVOKE ALL ON SCHEMA sales FROM sales_manager;

REASSIGN OWNED BY catalog_manager TO app_user;
REASSIGN OWNED BY sales_manager TO app_user;

ALTER SCHEMA catalog OWNER TO app_user;
ALTER SCHEMA sales OWNER TO app_user;

ALTER TABLE sales.orders DROP CONSTRAINT status_constraint;

DROP TABLE sales.order_items;
DROP TABLE sales.orders;

DROP SCHEMA sales;

DROP TABLE catalog.products;
DROP TABLE catalog.product_categories;
DROP TABLE catalog.warehouses;

DROP SCHEMA catalog;
