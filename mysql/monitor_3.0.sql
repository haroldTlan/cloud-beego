-- MySQL dump 10.13  Distrib 5.5.38, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: speediodb
-- ------------------------------------------------------
-- Server version	5.5.38-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `client`
--

DROP TABLE IF EXISTS `client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `client` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) DEFAULT NULL,
  `ip` varchar(64) DEFAULT NULL,
  `version` varchar(64) DEFAULT NULL,
  `size` varchar(64) DEFAULT NULL,
  `status` tinyint(3) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `devtype` varchar(64) DEFAULT 'client',
  `clusterid` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client`
--

LOCK TABLES `client` WRITE;
/*!40000 ALTER TABLE `client` DISABLE KEYS */;
/*!40000 ALTER TABLE `client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster`
--

DROP TABLE IF EXISTS `cluster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `cid` int(11) NOT NULL,
  `uuid` varchar(255) NOT NULL,
  `zoofs` tinyint(1) NOT NULL,
  `store` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster`
--

LOCK TABLES `cluster` WRITE;
/*!40000 ALTER TABLE `cluster` DISABLE KEYS */;
/*!40000 ALTER TABLE `cluster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `disks`
--

DROP TABLE IF EXISTS `disks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `disks` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `health` varchar(64) NOT NULL,
  `role` varchar(64) NOT NULL,
  `location` varchar(64) NOT NULL,
  `raid` varchar(64) NOT NULL,
  `cap_sector` bigint(20) NOT NULL,
  `cap_mb` double NOT NULL,
  `vendor` varchar(64) NOT NULL,
  `model` varchar(64) NOT NULL,
  `sn` varchar(64) NOT NULL,
  `machineid` varchar(64) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=301 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `disks`
--

LOCK TABLES `disks` WRITE;
/*!40000 ALTER TABLE `disks` DISABLE KEYS */;
/*!40000 ALTER TABLE `disks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dsus`
--

DROP TABLE IF EXISTS `dsus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dsus` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `location` varchar(255) NOT NULL,
  `support_disk_nr` int(11) NOT NULL,
  `machineid` varchar(255) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dsus`
--

LOCK TABLES `dsus` WRITE;
/*!40000 ALTER TABLE `dsus` DISABLE KEYS */;
/*!40000 ALTER TABLE `dsus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `emergency`
--

DROP TABLE IF EXISTS `emergency`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `emergency` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `level` varchar(50) DEFAULT NULL,
  `message` varchar(200) DEFAULT NULL,
  `chinese_message` varchar(200) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `ip` varchar(64) DEFAULT NULL,
  `event` varchar(64) DEFAULT NULL,
  `status` tinyint(3) DEFAULT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=2606 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `emergency`
--

LOCK TABLES `emergency` WRITE;
/*!40000 ALTER TABLE `emergency` DISABLE KEYS */;
/*!40000 ALTER TABLE `emergency` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `export`
--

DROP TABLE IF EXISTS `export`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `export` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) DEFAULT NULL,
  `ip` varchar(64) DEFAULT NULL,
  `version` varchar(64) DEFAULT NULL,
  `size` varchar(64) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `status` tinyint(3) DEFAULT '0',
  `devtype` varchar(64) DEFAULT 'export',
  `role` varchar(64) DEFAULT NULL,
  `virtual` varchar(64) DEFAULT NULL,
  `clusterid` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `export`
--

LOCK TABLES `export` WRITE;
/*!40000 ALTER TABLE `export` DISABLE KEYS */;
/*!40000 ALTER TABLE `export` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `filesystems`
--

DROP TABLE IF EXISTS `filesystems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `filesystems` (
  `uuid` varchar(64) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `machineId` varchar(64) DEFAULT NULL,
  `volume` varchar(64) DEFAULT NULL,
  `name` varchar(64) DEFAULT NULL,
  `chunk_kb` int(11) DEFAULT NULL,
  `mountpoint` varchar(64) DEFAULT NULL,
  `type` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `filesystems`
--

LOCK TABLES `filesystems` WRITE;
/*!40000 ALTER TABLE `filesystems` DISABLE KEYS */;
/*!40000 ALTER TABLE `filesystems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fs`
--

DROP TABLE IF EXISTS `fs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fs` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `volume` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `type` varchar(64) NOT NULL,
  `machineid` varchar(64) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fs`
--

LOCK TABLES `fs` WRITE;
/*!40000 ALTER TABLE `fs` DISABLE KEYS */;
/*!40000 ALTER TABLE `fs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `initiators`
--

DROP TABLE IF EXISTS `initiators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `initiators` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `portals` varchar(64) NOT NULL,
  `wwn` varchar(64) NOT NULL,
  `id` varchar(64) NOT NULL,
  `volumes` varchar(10) NOT NULL,
  `active` int(11) NOT NULL,
  `machineid` varchar(64) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=307 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `initiators`
--

LOCK TABLES `initiators` WRITE;
/*!40000 ALTER TABLE `initiators` DISABLE KEYS */;
/*!40000 ALTER TABLE `initiators` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `journal`
--

DROP TABLE IF EXISTS `journal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `journal` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `level` varchar(50) DEFAULT NULL,
  `message` varchar(200) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `machineId` varchar(64) DEFAULT '',
  `id` int(11) DEFAULT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `journal`
--

LOCK TABLES `journal` WRITE;
/*!40000 ALTER TABLE `journal` DISABLE KEYS */;
/*!40000 ALTER TABLE `journal` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `journals`
--

DROP TABLE IF EXISTS `journals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `journals` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `message` varchar(255) NOT NULL,
  `level` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `created_at` bigint(10) NOT NULL,
  `machineid` varchar(255) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=1900 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `journals`
--

LOCK TABLES `journals` WRITE;
/*!40000 ALTER TABLE `journals` DISABLE KEYS */;
/*!40000 ALTER TABLE `journals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `machine`
--

DROP TABLE IF EXISTS `machine`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `machine` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) DEFAULT NULL,
  `ip` varchar(64) DEFAULT NULL,
  `slotnr` int(10) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `devtype` varchar(64) DEFAULT '',
  `status` tinyint(3) DEFAULT '1',
  `role` varchar(64) DEFAULT NULL,
  `clusterid` varchar(64) DEFAULT '',
  PRIMARY KEY (`uid`),
  KEY `machine_created` (`created`)
) ENGINE=InnoDB AUTO_INCREMENT=66 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `machine`
--

LOCK TABLES `machine` WRITE;
/*!40000 ALTER TABLE `machine` DISABLE KEYS */;
/*!40000 ALTER TABLE `machine` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mail`
--

DROP TABLE IF EXISTS `mail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mail` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `address` varchar(64) DEFAULT NULL,
  `level` int(10) DEFAULT NULL,
  `ttl` int(10) DEFAULT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mail`
--

LOCK TABLES `mail` WRITE;
/*!40000 ALTER TABLE `mail` DISABLE KEYS */;
/*!40000 ALTER TABLE `mail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `raids`
--

DROP TABLE IF EXISTS `raids`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `raids` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `health` varchar(64) NOT NULL,
  `level` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `cap` bigint(20) NOT NULL,
  `used` bigint(20) NOT NULL,
  `cap_mb` double NOT NULL,
  `used_mb` double NOT NULL,
  `machineid` varchar(64) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `raids`
--

LOCK TABLES `raids` WRITE;
/*!40000 ALTER TABLE `raids` DISABLE KEYS */;
/*!40000 ALTER TABLE `raids` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `storage`
--

DROP TABLE IF EXISTS `storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `storage` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) DEFAULT NULL,
  `ip` varchar(64) DEFAULT NULL,
  `version` varchar(64) DEFAULT NULL,
  `size` varchar(64) DEFAULT NULL,
  `master` varchar(64) DEFAULT NULL,
  `cid` int(10) DEFAULT NULL,
  `sid` int(10) DEFAULT NULL,
  `slot` varchar(64) DEFAULT NULL,
  `status` tinyint(3) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `devtype` varchar(64) DEFAULT 'storage',
  `clusterid` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `storage`
--

LOCK TABLES `storage` WRITE;
/*!40000 ALTER TABLE `storage` DISABLE KEYS */;
/*!40000 ALTER TABLE `storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `threshhold`
--

DROP TABLE IF EXISTS `threshhold`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `threshhold` (
  `uid` int(10) NOT NULL AUTO_INCREMENT,
  `dev` varchar(64) NOT NULL,
  `warning` double DEFAULT NULL,
  `normal` double DEFAULT NULL,
  `type` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `threshhold`
--

LOCK TABLES `threshhold` WRITE;
/*!40000 ALTER TABLE `threshhold` DISABLE KEYS */;
INSERT INTO `threshhold` VALUES (1,'cpu',16,0,'export','处理器'),(2,'mem',100,90,'export','内存'),(3,'systemCap',100,92,'export','系统盘容量'),(4,'dockerCap',100,90,'export','docker文件夹容量'),(5,'tmpCap',91,90,'export','tmp文件夹容量'),(6,'varCap',100,80,'export','var文件夹容量'),(7,'weedCpu',100,90,'export','minio处理器占用率'),(8,'weedMem',60,20,'export','minio内存占用率'),(9,'cpu',1,0,'storage','处理器'),(10,'mem',100,80,'storage','内存'),(11,'systemCap',100,80,'storage','系统盘容量'),(12,'filesystemCap',100,93,'storage','文件系统容量'),(13,'weedCpu',100,92,'storage','weed处理器占用率'),(14,'weedMem',92,90,'storage','weed内存占用率'),(15,'cache',92,90,'storage','缓存');
/*!40000 ALTER TABLE `threshhold` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `volumes`
--

DROP TABLE IF EXISTS `volumes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `volumes` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) NOT NULL,
  `health` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `cap` bigint(10) NOT NULL,
  `cap_mb` double NOT NULL,
  `owner` varchar(64) NOT NULL,
  `used` int(11) NOT NULL,
  `machineid` varchar(64) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=132 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `volumes`
--

LOCK TABLES `volumes` WRITE;
/*!40000 ALTER TABLE `volumes` DISABLE KEYS */;
/*!40000 ALTER TABLE `volumes` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-05-05  8:48:54
