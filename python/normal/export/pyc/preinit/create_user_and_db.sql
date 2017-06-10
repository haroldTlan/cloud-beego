CREATE USER zonion@localhost IDENTIFIED BY 'passwd';

DROP DATABASE IF EXISTS speediodb;
CREATE DATABASE speediodb;
GRANT ALL PRIVILEGES ON speediodb.* TO zonion@localhost IDENTIFIED BY 'passwd';

DROP DATABASE IF EXISTS monfsdb;
CREATE DATABASE monfsdb;
GRANT ALL PRIVILEGES ON monfsdb.* TO zonion@localhost IDENTIFIED BY 'passwd';

FLUSH PRIVILEGES;
