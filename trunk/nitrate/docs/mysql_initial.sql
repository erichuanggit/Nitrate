/* MySQL initial script */
--
-- Upgrade to 2.0
--
-- Empty the permission table
-- TRUNCATE auth_permission;
-- TRUNCATE auth_group_permissions;

-- Add columns new app need
ALTER TABLE test_plans ADD extra_link varchar(1024);
ALTER TABLE test_runs ADD estimated_time time DEFAULT '00:00:00';
ALTER TABLE test_attachments ADD stored_name mediumtext;

--
-- Upgrade to 3.0
--

-- Rename the columns name to fit the ORM
ALTER TABLE test_case_runs CHANGE assignee assignee_id mediumint(9);
ALTER TABLE test_case_runs CHANGE testedby tested_by_id mediumint(9);

-- Add WAIVED case run status(Bug #577272)
INSERT INTO test_case_run_status (name, sortkey, description) VALUES ('WAIVED', 8, NULL);

-- Add Primary Key to test case bugs and other necessary columns for outside bug system support
ALTER TABLE test_case_bugs ADD id int NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST;
ALTER TABLE test_case_bugs ADD bug_system_id int NOT NULL;
ALTER TABLE test_case_bugs ADD summary varchar(255);
ALTER TABLE test_case_bugs ADD description mediumtext;
CREATE INDEX case_bugs_case_bug_system_id_idx ON test_case_bugs (bug_system_id);

-- After syncdb process
-- INSERT INTO test_case_bug_systems (name, url_reg_exp) values ('Red Hat Bugzilla', 'https://bugzilla.redhat.com/show_bug.cgi?id=%s');
-- UPDATE test_case_bugs SET bug_system_id = 1;
ALTER TABLE test_tags CHANGE tag_name tag_name VARCHAR(255) CHARACTER SET latin1 COLLATE latin1_general_cs;

-- Upgrade to 3.0.2
ALTER TABLE test_cases ADD is_automated_proposed tinyint(4) NOT NULL DEFAULT 0 AFTER isautomated;

-- Upgrade to 3.0.3
ALTER TABLE test_case_run_status ADD auto_blinddown tinyint(4) NOT NULL DEFAULT 1;
UPDATE test_case_run_status SET auto_blinddown = 0 WHERE name = 'RUNNING';

-- Upgrade to 3.0.4
ALTER TABLE test_cases ADD notes mediumtext;

-- Upgrade to 3.1.1
ALTER TABLE test_plans ADD COLUMN parent_id int unsigned;