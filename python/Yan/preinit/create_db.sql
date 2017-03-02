/*CREATE USER zonion@localhost IDENTIFIED BY 'passwd';*/

DROP DATABASE IF EXISTS speediodb;
CREATE DATABASE speediodb;
GRANT ALL PRIVILEGES ON speediodb.* TO zonion@localhost IDENTIFIED BY 'passwd';

DROP DATABASE IF EXISTS monfsdb;
CREATE DATABASE monfsdb;
GRANT ALL PRIVILEGES ON monfsdb.* TO zonion@localhost IDENTIFIED BY 'passwd';

DROP DATABASE IF EXISTS sync_lundb;
CREATE DATABASE sync_lundb;
GRANT ALL PRIVILEGES ON sync_lundb.* TO zonion@localhost IDENTIFIED BY 'passwd';

DROP DATABASE IF EXISTS zero_diskdb;
CREATE DATABASE zero_diskdb;
GRANT ALL PRIVILEGES ON zero_diskdb.* TO zonion@localhost IDENTIFIED BY 'passwd';

FLUSH PRIVILEGES;
