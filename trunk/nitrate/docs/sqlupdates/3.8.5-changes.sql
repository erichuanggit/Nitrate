USE testopia;

-- Performance improvement by removing triggers added previously
ALTER TABLE test_runs DROP COLUMN case_run_status;
DROP TRIGGER case_run_status_trigger_update;
DROP TRIGGER case_run_status_trigger_insert;
DROP TRIGGER case_run_status_trigger_delete;

-- Update auth_user to change encoding of all fields with varchar type to UTF8;
ALTER TABLE auth_user MODIFY first_name VARCHAR(30) CHARACTER SET utf8;
ALTER TABLE auth_user MODIFY last_name VARCHAR(30) CHARACTER SET utf8;
ALTER TABLE auth_user MODIFY username VARCHAR(30) CHARACTER SET utf8;
ALTER TABLE auth_user MODIFY password VARCHAR(128) CHARACTER SET utf8;
ALTER TABLE auth_user MODIFY email VARCHAR(75) CHARACTER SET utf8;