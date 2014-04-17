-- Downgrade database schemas from v3.8.7-hotfix to v3.8.7.

-- Drop composite index on content_type_id, object_pk and site_id.
DROP INDEX `tcms_bookmarks_62ffa694` ON `tcms_bookmarks`;
DROP INDEX `tcms_logs_62ffa694` ON `tcms_logs`;
DROP INDEX `tcms_contacts_62ffa694` ON `tcms_contacts`;
DROP INDEX `tcms_linkrefs_62ffa694` ON `tcms_linkrefs`;

-- Cause by converting data type, index `object_pk` can not work with text
-- that did not specify a key length.
DROP INDEX object_pk ON tcms_logs;

-- Convert column `object_pk` data type from int(11) to text.
ALTER TABLE `tcms_linkrefs` MODIFY COLUMN `object_pk` text;
ALTER TABLE `tcms_logs` MODIFY COLUMN `object_pk` text;
ALTER TABLE `tcms_bookmarks` MODIFY COLUMN `object_pk` text;
ALTER TABLE `tcms_contacts` MODIFY COLUMN `object_pk` text;

-- Rebuild the index on object_pk with key length 20.
CREATE INDEX `object_pk` ON `tcms_logs` (`object_pk`(20));