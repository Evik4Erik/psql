ALTER TABLE sales.orders DROP CONSTRAINT created_by_user;
ALTER TABLE sales.orders DROP COLUMN created_by;

REVOKE SELECT ON TABLE auth.users to PUBLIC;
REVOKE USAGE ON SCHEMA auth TO PUBLIC;

DROP TABLE auth.users;
DROP SCHEMA auth;
