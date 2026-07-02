REVOKE USAGE ON SCHEMA inventory FROM worker;
REVOKE SELECT, UPDATE ON ALL TABLES IN SCHEMA inventory FROM worker;

DROP TABLE IF EXISTS  inventory.reserves;
DROP TABLE IF EXISTS  inventory.delivery_items;
DROP TABLE IF EXISTS  inventory.transfer_items;
DROP TABLE IF EXISTS  inventory.transfers; 
DROP TABLE IF EXISTS  inventory.deliveries;

DROP TABLE IF EXISTS  inventory.stocks;
DROP TABLE IF EXISTS  inventory.routes;

REVOKE ALL ON SCHEMA inventory FROM inventory_manager;
REVOKE All ON ALL TABLES IN SCHEMA inventory FROM inventory_manager;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA inventory FROM inventory_manager;

REVOKE USAGE ON SCHEMA catalog FROM inventory_manager;

DROP SCHEMA IF EXISTS inventory;

ALTER TABLE catalog.warehouses ADD COLUMN city TEXT;

UPDATE catalog.warehouses
SET city = 
    CASE 
        WHEN city_id = 1 THEN 'Москва'            
        WHEN city_id = 2 THEN 'Санкт-Петербург'   
        WHEN city_id = 3 THEN 'Новосибирск'      
        WHEN city_id = 4 THEN 'Екатеринбург'     
        WHEN city_id = 5 THEN 'Казань'            
        WHEN city_id = 6 THEN 'Нижний Новгород'  
        WHEN city_id = 7 THEN 'Челябинск'        
        WHEN city_id = 8 THEN 'Самара'           
        WHEN city_id = 9 THEN 'Омск'              
        WHEN city_id = 10 THEN 'Ростов-на-Дону'    
        WHEN city_id = 11 THEN 'Уфа'               
        WHEN city_id = 12 THEN 'Красноярск'       
        WHEN city_id = 13 THEN 'Воронеж'        
        WHEN city_id = 14 THEN 'Пермь'           
        WHEN city_id = 15 THEN 'Волгоград'     
        ELSE 'Москва'
    END;

ALTER TABLE catalog.warehouses DROP COLUMN city_id;

REVOKE All PRIVILEGES ON TABLE catalog.cities FROM catalog_manager;
REVOKE SELECT ON TABLE catalog.cities  FROM sales_manager;

DROP TABLE IF EXISTS  catalog.cities;
