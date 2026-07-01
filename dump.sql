-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: procurement
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tab_attachment`
--

DROP TABLE IF EXISTS `tab_attachment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_attachment` (
  `entity` varchar(50) NOT NULL,
  `entity_id` bigint NOT NULL,
  `purchase_order_id` bigint NOT NULL,
  `filename` varchar(255) NOT NULL,
  `file_key` varchar(500) NOT NULL,
  `url` varchar(1000) NOT NULL,
  `content_type` varchar(100) NOT NULL,
  `size` bigint NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_attachment_entity_id` (`entity_id`),
  KEY `ix_tab_attachment_entity` (`entity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_attachment`
--

LOCK TABLES `tab_attachment` WRITE;
/*!40000 ALTER TABLE `tab_attachment` DISABLE KEYS */;
/*!40000 ALTER TABLE `tab_attachment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_audit_log`
--

DROP TABLE IF EXISTS `tab_audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_audit_log` (
  `entity` varchar(50) NOT NULL,
  `entity_id` bigint NOT NULL,
  `action` varchar(20) NOT NULL,
  `message` text NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_audit_log_entity_id` (`entity_id`),
  KEY `ix_tab_audit_log_entity` (`entity`)
) ENGINE=InnoDB AUTO_INCREMENT=87 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_audit_log`
--

LOCK TABLES `tab_audit_log` WRITE;
/*!40000 ALTER TABLE `tab_audit_log` DISABLE KEYS */;
INSERT INTO `tab_audit_log` VALUES ('purchase_order',1,'create','',1,'2026-06-30 05:18:36',1,'2026-06-30 05:18:36',1),('purchase_order',1,'submitted','',2,'2026-06-30 05:18:36',1,'2026-06-30 05:18:36',1),('purchase_order',1,'approved','',3,'2026-06-30 05:18:36',1,'2026-06-30 05:18:36',1),('purchase_order',2,'create','',4,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('purchase_order',2,'submitted','',5,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('purchase_order',2,'approved','',6,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('purchase_order',2,'update','',7,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('payment_request',1,'create','',8,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('payment_request',1,'submitted','',9,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('payment_request',1,'approved','',10,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('payment_request',1,'paid','',11,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('payment_request',2,'create','',12,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',1),('purchase_order',1,'create','',13,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',1),('purchase_order',1,'submitted','',14,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',1),('purchase_order',1,'approved','',15,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',1),('purchase_order',1,'update','',16,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',1),('purchase_order',1,'delete','',17,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',1),('purchase_order',1,'create','',18,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',2,'create','',19,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',2,'submitted','',20,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',2,'approved','',21,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',2,'update','',22,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',3,'create','',23,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',3,'submitted','',24,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',3,'approved','',25,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_order',3,'update','',26,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('survey',1,'create','',27,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('survey',1,'submitted','',28,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('survey',2,'create','',29,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('purchase_request',1,'create','',30,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('purchase_request',1,'submitted','',31,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('purchase_request',2,'create','',32,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('purchase_request',2,'submitted','',33,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('purchase_request',2,'approved','',34,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('purchase_request',3,'create','',35,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('purchase_order',1,'create','',36,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',1,'submitted','',37,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',1,'approved','',38,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',1,'update','',39,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',2,'create','',40,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',2,'submitted','',41,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',2,'approved','',42,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',2,'update','',43,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',3,'create','',44,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',1),('purchase_order',1,'create','',45,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',1,'submitted','',46,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',1,'approved','',47,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',1,'update','',48,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',2,'create','',49,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',2,'submitted','',50,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',2,'approved','',51,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',2,'update','',52,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',1),('purchase_order',3,'create','',53,'2026-06-30 09:30:38',1,'2026-06-30 09:30:38',1),('item_group',11,'update','',54,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('purchase_order',1,'create','',55,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('purchase_order',1,'submitted','',56,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('purchase_order',1,'approved','',57,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('purchase_order',1,'update','',58,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('purchase_order',2,'create','',59,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('purchase_order',2,'submitted','',60,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',1),('purchase_order',2,'approved','',61,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',1),('purchase_order',2,'update','',62,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',1),('company',30,'create','',63,'2026-06-30 09:51:42',1,'2026-06-30 09:51:42',1),('company',31,'create','',64,'2026-06-30 09:53:10',1,'2026-06-30 09:53:10',1),('company',32,'create','',65,'2026-06-30 09:55:49',1,'2026-06-30 09:55:49',1),('company',33,'create','',66,'2026-06-30 09:57:23',1,'2026-06-30 09:57:23',1),('company',33,'delete','',67,'2026-06-30 09:57:28',1,'2026-06-30 09:57:28',1),('purchase_order',2,'cancelled','test',68,'2026-06-30 10:03:35',1,'2026-06-30 10:03:35',1),('purchase_order',2,'draft','',69,'2026-06-30 10:03:35',1,'2026-06-30 10:03:35',1),('purchase_order',2,'submitted','',70,'2026-06-30 10:03:57',1,'2026-06-30 10:03:57',1),('purchase_order',2,'approved','',71,'2026-06-30 10:03:57',1,'2026-06-30 10:03:57',1),('company',27,'update','',72,'2026-06-30 10:04:26',1,'2026-06-30 10:04:26',1),('company',27,'update','',73,'2026-06-30 10:04:31',1,'2026-06-30 10:04:31',1),('purchase_order',2,'completed','',74,'2026-06-30 10:07:08',1,'2026-06-30 10:07:08',1),('purchase_order',2,'draft','',75,'2026-06-30 10:07:09',1,'2026-06-30 10:07:09',1),('purchase_order',2,'update','',76,'2026-06-30 10:07:37',1,'2026-06-30 10:07:37',1),('purchase_order',2,'submitted','',77,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',1),('purchase_order',2,'approved','',78,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',1),('purchase_order',2,'update','',79,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',1),('purchase_order',2,'completed','',80,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',1),('purchase_order',2,'draft','',81,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',1),('purchase_order',2,'submitted','',82,'2026-06-30 10:08:20',1,'2026-06-30 10:08:20',1),('purchase_order',2,'approved','',83,'2026-06-30 10:08:20',1,'2026-06-30 10:08:20',1),('purchase_order',1,'update','',84,'2026-06-30 10:29:33',1,'2026-06-30 10:29:33',1),('purchase_order',2,'update','',85,'2026-06-30 10:29:33',1,'2026-06-30 10:29:33',1),('payment_request',1,'create','',86,'2026-06-30 10:29:33',1,'2026-06-30 10:29:33',1);
/*!40000 ALTER TABLE `tab_audit_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_brand`
--

DROP TABLE IF EXISTS `tab_brand`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_brand` (
  `code` varchar(25) NOT NULL,
  `department` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  `manager_id` bigint DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_brand`
--

LOCK TABLES `tab_brand` WRITE;
/*!40000 ALTER TABLE `tab_brand` DISABLE KEYS */;
INSERT INTO `tab_brand` VALUES ('NM','Nhà máy Dego',1,11,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('SX','SX - Ms Ly',1,12,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('LAB','Lab',1,13,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('AB','KD ABA',1,14,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('IC','KD ICARE',1,15,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('DR','KD DR XANH',1,16,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('ID','KD IDA',1,17,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('TM','TM - Ms Quyên',1,18,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('N2','KD N2SBIO',1,19,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0),('QLTM_Ms Ngân','QLTM_Ms Ngân',1,20,'2026-07-01 01:14:49',0,'2026-07-01 01:14:49',0,0);
/*!40000 ALTER TABLE `tab_brand` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_company`
--

DROP TABLE IF EXISTS `tab_company`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_company` (
  `code` varchar(25) NOT NULL,
  `name` varchar(255) NOT NULL,
  `tax_code` varchar(25) NOT NULL,
  `address` text NOT NULL,
  `invoice_email` varchar(255) NOT NULL,
  `parent` bigint NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_company`
--

LOCK TABLES `tab_company` WRITE;
/*!40000 ALTER TABLE `tab_company` DISABLE KEYS */;
INSERT INTO `tab_company` VALUES ('DEGO','DEGO HOLDING','','','',0,1,1,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),('IDA','CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL','0314562909','','',0,1,2,'2026-06-29 13:45:11',0,'2026-06-29 13:45:11',0),('ABA','CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA','0316342296','','',0,1,3,'2026-06-29 13:45:11',0,'2026-06-29 13:45:11',0),('DEGO HOLDING','CÔNG TY TNHH DEGO HOLDING','1801722464','B19 đường dẫn cầu Cần Thơ, QL1A, Khu dân cư Trung tâm văn hóa Tây Đô, Phường Cái Răng, Thành phố Cần Thơ, Việt Nam.','',0,1,20,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('ICARE','CÔNG TY TNHH DƯỢC PHẨM ICARE','0315593265','108 Trần Đình Xu, Phường Cầu Ông Lãnh, Thành phố Hồ Chí Minh, Việt Nam','',0,1,21,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('NPP DR.XANH','NHÀ PHÂN PHỐI DR XANH','578010406','Số 124, Đường Võ Văn Kiệt, khu vực Bình Trung, Phường Long Hòa, Quận Bình Thủy, TP.Cần Thơ','',0,1,22,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('HỘ KD DR.XANH','HỘ KINH DOANH DR XANH','578005750','Ấp Qui Lân 1, Xã Thạnh Quới, Huyện Vĩnh Thạnh, TP Cần Thơ, Việt Nam','',0,1,23,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('BAMBOO','CÔNG TY TNHH XUẤT NHẬP KHẨU SẢN XUẤT THƯƠNG MẠI BAMBOO VIỆT NAM','0318629897','Tầng 18, Tòa nhà ROX Tower, 180-192 Nguyễn Công Trứ, Phường Bến Thành, Thành phó Hồ Chí Minh, Việt Nam.','',0,1,24,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('N2SBIO','CÔNG TY TNHH N2SBIO VIỆT NAM','0318776965','108 Trần Đình Xu, Phường Nguyễn Cư Trinh, Quận 1, TP Hồ Chí Minh','',0,1,25,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('NN DEGO','CÔNG TY TNHH SẢN XUẤT VÀ XUẤT NHẬP KHẨU HOÁ CHẤT NÔNG NGHIỆP DEGO','0318430011','Tầng 9, tòa nhà K&M Tower, 33 Ung Văn Khiêm, Phường Thạnh Mỹ Tây, TP Hồ Chí Minh, Việt Nam','',0,1,26,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('NN ABA','CÔNG TY TNHH HÓA CHẤT NÔNG NGHIỆP ABA','1801818328','B18 đường dẫn cầu Cần Thơ, QL1A, Khu dân cư Trung tâm văn hóa Tây Đô, Phường Cái Răng, Thành phố Cần Thơ, Việt Nam.','',0,1,27,'2026-06-30 03:01:07',0,'2026-06-30 10:04:31',1);
/*!40000 ALTER TABLE `tab_company` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_department`
--

DROP TABLE IF EXISTS `tab_department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_department` (
  `code` varchar(25) NOT NULL,
  `name` varchar(255) NOT NULL,
  `company_id` bigint NOT NULL,
  `parent` bigint NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_department`
--

LOCK TABLES `tab_department` WRITE;
/*!40000 ALTER TABLE `tab_department` DISABLE KEYS */;
/*!40000 ALTER TABLE `tab_department` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_email_log`
--

DROP TABLE IF EXISTS `tab_email_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_email_log` (
  `event` varchar(100) NOT NULL,
  `to_email` varchar(255) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `status` varchar(20) NOT NULL,
  `error` text,
  `sent_at` datetime DEFAULT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_email_log`
--

LOCK TABLES `tab_email_log` WRITE;
/*!40000 ALTER TABLE `tab_email_log` DISABLE KEYS */;
INSERT INTO `tab_email_log` VALUES ('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,1,'2026-06-30 05:18:36',1,'2026-06-30 05:18:36',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,2,'2026-06-30 05:18:36',1,'2026-06-30 05:18:36',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,3,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,4,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,5,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,6,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,7,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,8,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00003','failed','SMTP credentials not configured in settings.',NULL,9,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00003','failed','SMTP credentials not configured in settings.',NULL,10,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),('survey_submitted','hgbao.idagroup@gmail.com','[Yêu cầu phê duyệt] Khảo sát KS00001','failed','SMTP credentials not configured in settings.',NULL,11,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),('pr_submitted','hgbao.idagroup@gmail.com','[GẤP] [Yêu cầu phê duyệt] PYC PYC00001','failed','SMTP credentials not configured in settings.',NULL,12,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',0),('pr_submitted','hgbao.idagroup@gmail.com','[Yêu cầu phê duyệt] PYC PYC00002','failed','SMTP credentials not configured in settings.',NULL,13,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',0),('pr_approved','hgbao.idagroup@gmail.com','[Đã duyệt] PYC PYC00002','failed','SMTP credentials not configured in settings.',NULL,14,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,15,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,16,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,17,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,18,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,19,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,20,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,21,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,22,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,23,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00001','failed','SMTP credentials not configured in settings.',NULL,24,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,25,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,26,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,27,'2026-06-30 10:03:57',1,'2026-06-30 10:03:57',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,28,'2026-06-30 10:03:57',1,'2026-06-30 10:03:57',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,29,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,30,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',0),('po_submitted','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,31,'2026-06-30 10:08:20',1,'2026-06-30 10:08:20',0),('po_approved','hgbao.idagroup@gmail.com','Thông báo mới: PO00002','failed','SMTP credentials not configured in settings.',NULL,32,'2026-06-30 10:08:20',1,'2026-06-30 10:08:20',0);
/*!40000 ALTER TABLE `tab_email_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_employee`
--

DROP TABLE IF EXISTS `tab_employee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_employee` (
  `code` varchar(25) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(25) NOT NULL,
  `company_id` bigint NOT NULL,
  `department_id` bigint NOT NULL,
  `position` varchar(100) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_employee`
--

LOCK TABLES `tab_employee` WRITE;
/*!40000 ALTER TABLE `tab_employee` DISABLE KEYS */;
INSERT INTO `tab_employee` VALUES ('degoadmin','Quản trị viên','','',1,0,'Admin',1,1,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0);
/*!40000 ALTER TABLE `tab_employee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_goods_receipt`
--

DROP TABLE IF EXISTS `tab_goods_receipt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_goods_receipt` (
  `code` varchar(50) NOT NULL,
  `po_id` bigint NOT NULL,
  `po_code` varchar(50) NOT NULL,
  `delivery_id` bigint NOT NULL,
  `company_id` bigint NOT NULL,
  `warehouse_code` varchar(50) NOT NULL,
  `product_code` varchar(50) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `unit` varchar(25) NOT NULL,
  `qty_received` decimal(18,3) NOT NULL,
  `received_date` varchar(10) NOT NULL,
  `qc_result` varchar(20) NOT NULL,
  `note` text NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_tab_goods_receipt_delivery_id` (`delivery_id`),
  KEY `ix_tab_goods_receipt_po_id` (`po_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_goods_receipt`
--

LOCK TABLES `tab_goods_receipt` WRITE;
/*!40000 ALTER TABLE `tab_goods_receipt` DISABLE KEYS */;
INSERT INTO `tab_goods_receipt` VALUES ('GR00001',1,'PO00001',1,27,'ADU','THC0004','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Cái',600.000,'2026-06-12','Đạt','',1,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('GR00002',2,'PO00002',2,27,'ADU','THC0004','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Cái',400.000,'2026-06-12','Đạt','',2,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',1);
/*!40000 ALTER TABLE `tab_goods_receipt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_inventory`
--

DROP TABLE IF EXISTS `tab_inventory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_inventory` (
  `company_id` bigint NOT NULL,
  `warehouse_code` varchar(50) NOT NULL,
  `product_code` varchar(50) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `unit` varchar(25) NOT NULL,
  `qty` decimal(18,3) NOT NULL,
  `avg_cost` decimal(18,2) NOT NULL,
  `value` decimal(18,2) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_inventory_warehouse_code` (`warehouse_code`),
  KEY `ix_tab_inventory_company_id` (`company_id`),
  KEY `ix_tab_inventory_product_code` (`product_code`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_inventory`
--

LOCK TABLES `tab_inventory` WRITE;
/*!40000 ALTER TABLE `tab_inventory` DISABLE KEYS */;
INSERT INTO `tab_inventory` VALUES (27,'ADU','THC0004','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Cái',1000.000,10800.00,10800000.00,1,'2026-06-30 09:47:22',0,'2026-06-30 09:47:23',0);
/*!40000 ALTER TABLE `tab_inventory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_inventory_move`
--

DROP TABLE IF EXISTS `tab_inventory_move`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_inventory_move` (
  `company_id` bigint NOT NULL,
  `warehouse_code` varchar(50) NOT NULL,
  `product_code` varchar(50) NOT NULL,
  `qty` decimal(18,3) NOT NULL,
  `unit_price` decimal(18,2) NOT NULL,
  `ref_type` varchar(20) NOT NULL,
  `ref_id` bigint NOT NULL,
  `note` text NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_inventory_move_company_id` (`company_id`),
  KEY `ix_tab_inventory_move_product_code` (`product_code`),
  KEY `ix_tab_inventory_move_warehouse_code` (`warehouse_code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_inventory_move`
--

LOCK TABLES `tab_inventory_move` WRITE;
/*!40000 ALTER TABLE `tab_inventory_move` DISABLE KEYS */;
INSERT INTO `tab_inventory_move` VALUES (27,'ADU','THC0004',600.000,10000.00,'gr',1,'Nhận hàng từ PO',1,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),(27,'ADU','THC0004',400.000,12000.00,'gr',2,'Nhận hàng từ PO',2,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',1);
/*!40000 ALTER TABLE `tab_inventory_move` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_item_group`
--

DROP TABLE IF EXISTS `tab_item_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_item_group` (
  `code` varchar(25) NOT NULL,
  `name` varchar(100) NOT NULL,
  `std_days` varchar(20) NOT NULL,
  `std_days_unavail` varchar(20) NOT NULL,
  `note` text NOT NULL,
  `apply_date` varchar(20) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_item_group`
--

LOCK TABLES `tab_item_group` WRITE;
/*!40000 ALTER TABLE `tab_item_group` DISABLE KEYS */;
INSERT INTO `tab_item_group` VALUES ('PL001','Nhãn','7','','','01/03/2026',1,3,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL002','Nhãn Metalize','12','','','01/03/2026',1,4,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL003','Nhãn Thùng','7','','','01/03/2026',1,5,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL004','Túi flexo','15','','Nhãn túi (Tân Đức)\n<5.000 túi: 12 ngày\n> 5.000 túi: 15 ngày','01/01/2026',1,6,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL005','Túi trục','21','','Làm trục: 12 - 15 ngày\nIn túi: 3 -5 ngày\nCắt: 1-2 ngày','01/03/2026',1,7,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL006','Hộp','15','','','01/03/2026',1,8,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL007','Can/Xô','5','','Thông tin tham khảo từ Ms Ly/ Thu mua check lại','01/03/2026',1,9,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL008','NL','10','','Trong nước','01/03/2026',1,10,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL009','Thùng','5','7','Thời gian Sx: 15 ngày\nNhận hàng: 2 ngày','01/03/2026',1,11,'2026-06-30 09:46:37',0,'2026-06-30 09:47:22',1),('PL010','Chai Nhôm','8','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Nhận hàng 2 ngày\n(Thông tin tham khảo từ Ms Ly/ Thu mua check lại)','01/03/2026',1,12,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL011','Chai khác','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/03/2026',1,13,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL012','Nắp','7','','Nắp NCC giao chung hàng với chai.','01/03/2026',1,14,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL013','Cốc đong','7','','Cốc đong NCC giao chung hàng với chai.','01/03/2026',1,15,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL014','NL NK','59','','- Làm hợp đồng với NCC cũ: 5 ngày\n- Chuẩn bị hàng: 14 ngày\n- Giao hàng 20 ngày\n- Nhận hàng + thông quan: 20 ngày','01/03/2026',1,16,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL015','NL Icare','4','','Trong nước, công nợ','01/03/2026',1,17,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL016','Xốp ( bong bóng khí)','5','','','01/03/2026',1,18,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL017','Giấy nhiệt K100x150','5','','','01/03/2026',1,19,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL018','HDSD Antisol','10','','','01/03/2026',1,20,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL019','Tem phụ antisol','15','','','01/03/2026',1,21,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL020','Tem chống hàng giả','10','','','01/03/2026',1,22,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL021','Chai Pet có vòi','15','','','01/03/2026',1,23,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL022','Hộp trắng','10','','','01/03/2026',1,24,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL023','Màng co','20','','NCC quá tải chưa tìm được NCC mới giá cạnh tranh','01/03/2026',1,25,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL024','Túi in cuộn màng','14','','Nhãn túi','08/04/2026',1,26,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL025','Vận chuyển','','','','18/04/2026',1,27,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL026','Băng keo','5','','','01/03/2026',1,28,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL027','Cuộn PE','7','','','01/05/2026',1,29,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL028','Lon','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/06/2026',1,30,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL029','VTBB SX','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/06/2026',1,31,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL030','Túi Zip','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/06/2026',1,32,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL031','Túi PA','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','09/06/2026',1,33,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL032','Tank','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','09/06/2026',1,34,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL033','Chai Pet','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/03/2026',1,35,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL034','Chai Hdpe','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/03/2026',1,36,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL035','Chai Pape','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 5 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/03/2026',1,37,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL036','Chai Nhôm nhập khẩu','33','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Nhập khẩu : 25 ngày\n- Thanh toán 5 ngày\n- Nhận hàng 2 ngày\n(Thông tin tham khảo từ Ms Ly/ Thu mua check lại)','01/03/2026',1,38,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL037','Chai Pet giả nhôm','7','','','01/03/2026',1,39,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL038','Chai HD giả nhôm','7','','','01/03/2026',1,40,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL039','Chai Pape giả nhôm','7','','','01/03/2026',1,41,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL040','Nắp Hdpe','7','','Nắp NCC giao chung hàng với chai.','01/03/2026',1,42,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL041','Nắp Pet','7','','Nắp NCC giao chung hàng với chai.','01/03/2026',1,43,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL042','Can HDPE','5','','Thông tin tham khảo từ Ms Ly/ Thu mua check lại','01/03/2026',1,44,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL043','Xô HDPE','5','','Thông tin tham khảo từ Ms Ly/ Thu mua check lại','01/03/2026',1,45,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL044','Nhãn giấy','7','','','01/03/2026',1,46,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL045','Nhãn Decal','7','','','01/03/2026',1,47,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL046','Nhãn Phụ','7','','','01/03/2026',1,48,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL047','Nhãn dán thùng','7','','','01/03/2026',1,49,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL048','Túi rời','15','','Nhãn túi (Tân Đức)\n<5.000 túi: 12 ngày\n> 5.000 túi: 15 ngày','01/01/2026',1,50,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL049','Túi in cuộn (không trục)','14','','Nhãn túi','01/03/2026',1,51,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL050','Túi PE (Túi nilong)','7','','','01/03/2026',1,52,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL051','Túi PA 3 biên','7','','','01/03/2026',1,53,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL052','Hộp carton 3 lớp','15','','','01/03/2026',1,54,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL053','Hộp giấy D','15','','','01/03/2026',1,55,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL054','Hộp đóng gói nâu','15','','','01/03/2026',1,56,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL055','Hộp icare: giấy Ivory','10','','','01/03/2026',1,57,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL056','Thùng carton 5 lớp','18','','Thời gian Sx: 15 ngày\nNhận hàng: 2 ngày','01/03/2026',1,58,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL057','Thùng carton 3 lớp','18','','Thời gian Sx: 15 ngày\nNhận hàng: 2 ngày','01/03/2026',1,59,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL058','Lon HDPE','7','','Hàng cần thanh toán trước: \n- Làm hồ sơ 1 ngày\n- Thanh toán 4 ngày\n- Sản xuất 0 ngày\n- Nhận hàng 2 ngày','01/06/2026',1,60,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL059','Bao PP','7','','','01/06/2026',1,61,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL060','Bao PE','7','','','01/06/2026',1,62,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL061','Phuy','15','','','01/06/2026',1,63,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL062','Màng co nhiệt','20','','NCC quá tải chưa tìm được NCC mới giá cạnh tranh','01/03/2026',1,64,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL063','Màng PE cuộn','21','','','01/06/2026',1,65,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL064','Băng keo trong','7','','','01/06/2026',1,66,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL065','Băng keo in logo','7','','','01/06/2026',1,67,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL066','Keo sữa','7','','','01/06/2026',1,68,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL067','Tem Hologram bạc (tem chống hàng giả icare)','12','','','01/06/2026',1,69,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL068','Tem decal vỡ (tem Asahi)','12','','','01/06/2026',1,70,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL069','Tem decal giấy','12','','','01/06/2026',1,71,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL070','NL Nhập khẩu','59','','- Làm hợp đồng với NCC mới: 5 ngày\n- Chuẩn bị hàng: 14 ngày\n- Giao hàng 20 ngày\n- Nhận hàng + thông quan: 20 ngày\nĐối với đường bay thì 41 ngày','01/03/2026',1,72,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL071','Tag treo','10','','','01/03/2026',1,73,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL072','Hàng sẵn kho ncc','','','','',1,74,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0),('PL073','Hàng ko sẵn kho ncc','','','','',1,75,'2026-06-30 09:46:37',0,'2026-06-30 09:46:37',0);
/*!40000 ALTER TABLE `tab_item_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_notification`
--

DROP TABLE IF EXISTS `tab_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_notification` (
  `user_id` bigint DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `body` text NOT NULL,
  `link` varchar(500) DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_notification_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_notification`
--

LOCK TABLES `tab_notification` WRITE;
/*!40000 ALTER TABLE `tab_notification` DISABLE KEYS */;
INSERT INTO `tab_notification` VALUES (1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,1,'2026-06-30 05:18:36',1,'2026-06-30 05:18:36',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,2,'2026-06-30 05:18:36',1,'2026-06-30 05:18:36',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,3,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,4,'2026-06-30 05:19:48',1,'2026-06-30 05:19:48',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,5,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,6,'2026-06-30 06:38:14',1,'2026-06-30 06:38:14',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,7,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,8,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),(1,'Thông báo mới: PO00003','Chứng từ PO00003 vừa có thay đổi trạng thái.','/purchase-orders/3',0,9,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),(1,'Thông báo mới: PO00003','Chứng từ PO00003 vừa có thay đổi trạng thái.','/purchase-orders/3',0,10,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),(1,'[Yêu cầu phê duyệt] Khảo sát KS00001','Có một phiếu khảo sát mới (Mã số: KS00001) cần bạn phê duyệt.','/surveys-supplier/1',0,11,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',0),(1,'[GẤP] [Yêu cầu phê duyệt] PYC PYC00001','Có một yêu cầu mua hàng mới (Mã số: PYC00001) cần bạn phê duyệt.','/purchase-requests/1',0,12,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',0),(1,'[Yêu cầu phê duyệt] PYC PYC00002','Có một yêu cầu mua hàng mới (Mã số: PYC00002) cần bạn phê duyệt.','/purchase-requests/2',0,13,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',0),(1,'[Đã duyệt] PYC PYC00002','Yêu cầu mua hàng PYC00002 của bạn đã được phê duyệt.','/purchase-requests/2',0,14,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,15,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,16,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,17,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,18,'2026-06-30 08:55:22',1,'2026-06-30 08:55:22',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,19,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,20,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,21,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,22,'2026-06-30 09:30:37',1,'2026-06-30 09:30:37',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,23,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',0),(1,'Thông báo mới: PO00001','Chứng từ PO00001 vừa có thay đổi trạng thái.','/purchase-orders/1',0,24,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,25,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,26,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,27,'2026-06-30 10:03:57',1,'2026-06-30 10:03:57',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,28,'2026-06-30 10:03:57',1,'2026-06-30 10:03:57',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,29,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,30,'2026-06-30 10:08:07',1,'2026-06-30 10:08:07',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,31,'2026-06-30 10:08:20',1,'2026-06-30 10:08:20',0),(1,'Thông báo mới: PO00002','Chứng từ PO00002 vừa có thay đổi trạng thái.','/purchase-orders/2',0,32,'2026-06-30 10:08:20',1,'2026-06-30 10:08:20',0);
/*!40000 ALTER TABLE `tab_notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_payable`
--

DROP TABLE IF EXISTS `tab_payable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_payable` (
  `company_id` bigint NOT NULL,
  `supplier_code` varchar(50) NOT NULL,
  `supplier_name` varchar(255) NOT NULL,
  `source_type` varchar(20) NOT NULL,
  `ref_type` varchar(20) NOT NULL,
  `ref_id` bigint NOT NULL,
  `po_id` bigint NOT NULL,
  `po_code` varchar(50) NOT NULL,
  `invoice_no` varchar(50) NOT NULL,
  `incur_date` varchar(10) NOT NULL,
  `period` varchar(7) NOT NULL,
  `due_date` varchar(10) NOT NULL,
  `amount` decimal(18,2) NOT NULL,
  `vat` decimal(18,2) NOT NULL,
  `total` decimal(18,2) NOT NULL,
  `paid_amount` decimal(18,2) NOT NULL,
  `remaining` decimal(18,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_payable_supplier_code` (`supplier_code`),
  KEY `ix_tab_payable_ref_id` (`ref_id`),
  KEY `ix_tab_payable_incur_date` (`incur_date`),
  KEY `ix_tab_payable_period` (`period`),
  KEY `ix_tab_payable_status` (`status`),
  KEY `ix_tab_payable_company_id` (`company_id`),
  KEY `ix_tab_payable_due_date` (`due_date`),
  KEY `ix_tab_payable_po_code` (`po_code`),
  KEY `ix_tab_payable_source_type` (`source_type`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_payable`
--

LOCK TABLES `tab_payable` WRITE;
/*!40000 ALTER TABLE `tab_payable` DISABLE KEYS */;
INSERT INTO `tab_payable` VALUES (27,'XANH VIỆT VINA','CÔNG TY TNHH XANH VIỆT VINA','goods','delivery',1,1,'PO00001','HD-A','2026-06-12','2026','2026-06-12',6000000.00,480000.00,6480000.00,0.00,6480000.00,'Chờ TT',1,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),(27,'Grab','Grab','shipping','delivery',1,1,'PO00001','MISA-HD-A-THC0004','2026-06-12','2026','2026-06-12',50000.00,0.00,50000.00,0.00,50000.00,'Chờ TT',2,'2026-06-30 09:47:22',1,'2026-06-30 10:29:33',1),(27,'XANH VIỆT VINA','CÔNG TY TNHH XANH VIỆT VINA','goods','delivery',2,2,'PO00002','HD-B','2026-06-12','2026','2026-06-12',4800000.00,384000.00,5184000.00,0.00,5184000.00,'Chờ TT',3,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',1),(27,'Grab','Grab','shipping','delivery',2,2,'PO00002','MISA-HD-B-THC0004','2026-06-12','2026','2026-06-12',50000.00,0.00,50000.00,0.00,50000.00,'Chờ TT',4,'2026-06-30 09:47:23',1,'2026-06-30 10:29:33',1);
/*!40000 ALTER TABLE `tab_payable` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_payment_request`
--

DROP TABLE IF EXISTS `tab_payment_request`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_payment_request` (
  `code` varchar(50) NOT NULL,
  `supplier_code` varchar(50) NOT NULL,
  `supplier_name` varchar(255) NOT NULL,
  `company_id` bigint NOT NULL,
  `source_type` varchar(20) NOT NULL,
  `request_date` varchar(10) NOT NULL,
  `total` decimal(18,2) NOT NULL,
  `note` text NOT NULL,
  `status` varchar(20) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_payment_request_supplier_code` (`supplier_code`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_payment_request`
--

LOCK TABLES `tab_payment_request` WRITE;
/*!40000 ALTER TABLE `tab_payment_request` DISABLE KEYS */;
INSERT INTO `tab_payment_request` VALUES ('YCTT00001','XANH VIỆT VINA','CÔNG TY TNHH XANH VIỆT VINA',27,'goods','2026-06-30',5184000.00,'','draft',1,'2026-06-30 10:29:33',1,'2026-06-30 10:29:33',1);
/*!40000 ALTER TABLE `tab_payment_request` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_payment_request_line`
--

DROP TABLE IF EXISTS `tab_payment_request_line`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_payment_request_line` (
  `request_id` bigint NOT NULL,
  `payable_id` bigint NOT NULL,
  `po_code` varchar(50) NOT NULL,
  `invoice_no` varchar(50) NOT NULL,
  `amount` decimal(18,2) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_payment_request_line_request_id` (`request_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_payment_request_line`
--

LOCK TABLES `tab_payment_request_line` WRITE;
/*!40000 ALTER TABLE `tab_payment_request_line` DISABLE KEYS */;
INSERT INTO `tab_payment_request_line` VALUES (1,3,'PO00002','HD-B',5184000.00,1,'2026-06-30 10:29:33',1,'2026-06-30 10:29:33',1);
/*!40000 ALTER TABLE `tab_payment_request_line` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_permission`
--

DROP TABLE IF EXISTS `tab_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_permission` (
  `role_id` bigint NOT NULL,
  `entity` varchar(50) NOT NULL,
  `can_read` tinyint(1) NOT NULL,
  `can_create` tinyint(1) NOT NULL,
  `can_write` tinyint(1) NOT NULL,
  `can_delete` tinyint(1) NOT NULL,
  `can_approve` tinyint(1) NOT NULL,
  `can_print` tinyint(1) NOT NULL,
  `can_export` tinyint(1) NOT NULL,
  `scope` varchar(10) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_permission_role_id` (`role_id`),
  KEY `ix_tab_permission_entity` (`entity`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_permission`
--

LOCK TABLES `tab_permission` WRITE;
/*!40000 ALTER TABLE `tab_permission` DISABLE KEYS */;
INSERT INTO `tab_permission` VALUES (1,'company',1,1,1,1,1,1,1,'all',1,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'department',1,1,1,1,1,1,1,'all',2,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'employee',1,1,1,1,1,1,1,'all',3,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'user',1,1,1,1,1,1,1,'all',4,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'role',1,1,1,1,1,1,1,'all',5,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'supplier',1,1,1,1,1,1,1,'all',6,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'product',1,1,1,1,1,1,1,'all',7,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'contract',1,1,1,1,1,1,1,'all',8,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'purchase_request',1,1,1,1,1,1,1,'all',9,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'survey',1,1,1,1,1,1,1,'all',10,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'purchase_order',1,1,1,1,1,1,1,'all',11,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'goods_receipt',1,1,1,1,1,1,1,'all',12,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'inventory',1,1,1,1,1,1,1,'all',13,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'payable',1,1,1,1,1,1,1,'all',14,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'payment',1,1,1,1,1,1,1,'all',15,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'report',1,1,1,1,1,1,1,'all',16,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'setting',1,1,1,1,1,1,1,'all',17,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0),(1,'warehouse',1,1,1,1,1,1,1,'all',18,'2026-06-30 02:38:43',0,'2026-06-30 02:38:43',0),(1,'unit',1,1,1,1,1,1,1,'all',19,'2026-06-30 02:38:43',0,'2026-06-30 02:38:43',0),(1,'item_group',1,1,1,1,1,1,1,'all',20,'2026-06-30 02:38:43',0,'2026-06-30 02:38:43',0),(1,'brand',1,1,1,1,1,1,1,'all',21,'2026-06-30 02:38:43',0,'2026-06-30 02:38:43',0),(1,'payment_request',1,1,1,1,1,1,1,'all',22,'2026-06-30 05:17:23',0,'2026-06-30 05:17:23',0);
/*!40000 ALTER TABLE `tab_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_po_delivery`
--

DROP TABLE IF EXISTS `tab_po_delivery`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_po_delivery` (
  `po_id` bigint NOT NULL,
  `po_item_id` bigint NOT NULL,
  `delivery_no` bigint NOT NULL,
  `warehouse_code` varchar(50) NOT NULL,
  `carrier_code` varchar(50) NOT NULL,
  `carrier_name` varchar(255) NOT NULL,
  `ship_qty` decimal(18,3) NOT NULL,
  `ship_unit` varchar(25) NOT NULL,
  `received_qty` decimal(18,3) NOT NULL,
  `promised_date` varchar(10) NOT NULL,
  `expected_date` varchar(10) NOT NULL,
  `received_date` varchar(10) NOT NULL,
  `std_days` bigint NOT NULL,
  `regulated_date` varchar(10) NOT NULL,
  `diff_promise` bigint NOT NULL,
  `diff_regulated` bigint NOT NULL,
  `diff_required` bigint NOT NULL,
  `invoice_no` varchar(50) NOT NULL,
  `shipping_unit_price` decimal(18,2) NOT NULL,
  `shipping_amount` decimal(18,2) NOT NULL,
  `qc_result` varchar(20) NOT NULL,
  `status` varchar(30) NOT NULL,
  `extra_request` text NOT NULL,
  `progress_note` text NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_po_delivery_po_id` (`po_id`),
  KEY `ix_tab_po_delivery_po_item_id` (`po_item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_po_delivery`
--

LOCK TABLES `tab_po_delivery` WRITE;
/*!40000 ALTER TABLE `tab_po_delivery` DISABLE KEYS */;
INSERT INTO `tab_po_delivery` VALUES (1,1,1,'ADU','Grab','Grab',600.000,'Kiện',600.000,'2026-06-10','','2026-06-12',5,'2026-06-06',-2,-6,0,'',50000.00,50000.00,'Đạt','Đã nhận','','',1,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),(2,2,1,'ADU','Grab','Grab',400.000,'Kiện',400.000,'2026-06-10','','2026-06-12',7,'2026-06-08',-2,-4,0,'',50000.00,50000.00,'Đạt','Đã nhận','','',2,'2026-06-30 09:47:23',1,'2026-06-30 09:47:23',1);
/*!40000 ALTER TABLE `tab_po_delivery` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_po_item`
--

DROP TABLE IF EXISTS `tab_po_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_po_item` (
  `po_id` bigint NOT NULL,
  `product_code` varchar(50) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `invoice_name` varchar(255) NOT NULL,
  `item_group` varchar(100) NOT NULL,
  `spec` varchar(255) NOT NULL,
  `fg_code` varchar(50) NOT NULL,
  `invoice_no` varchar(50) NOT NULL,
  `supplier_ready` tinyint(1) NOT NULL,
  `required_date` varchar(10) NOT NULL,
  `unit` varchar(25) NOT NULL,
  `qty_request` decimal(18,3) NOT NULL,
  `qty_order` decimal(18,3) NOT NULL,
  `price` decimal(18,2) NOT NULL,
  `vat` decimal(5,2) NOT NULL,
  `amount` decimal(18,2) NOT NULL,
  `qty_received` decimal(18,3) NOT NULL,
  `qty_remaining` decimal(18,3) NOT NULL,
  `line_status` varchar(30) NOT NULL,
  `warehouse_code` varchar(50) NOT NULL,
  `note` varchar(255) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_po_item_po_id` (`po_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_po_item`
--

LOCK TABLES `tab_po_item` WRITE;
/*!40000 ALTER TABLE `tab_po_item` DISABLE KEYS */;
INSERT INTO `tab_po_item` VALUES (1,'THC0004','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Thùng','','','HD-A',1,'','Cái',1000.000,1000.000,10000.00,8.00,6480000.00,600.000,400.000,'Đang giao','ADU','',1,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),(2,'THC0004','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Thùng','','','HD-B',0,'','Cái',1000.000,1000.000,12000.00,8.00,5184000.00,400.000,600.000,'Đang giao','ADU','',2,'2026-06-30 09:47:22',1,'2026-06-30 09:47:23',1);
/*!40000 ALTER TABLE `tab_po_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_product`
--

DROP TABLE IF EXISTS `tab_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_product` (
  `code` varchar(50) NOT NULL,
  `name` varchar(255) NOT NULL,
  `invoice_name` varchar(255) NOT NULL,
  `legal_name` varchar(255) NOT NULL,
  `item_group` varchar(50) NOT NULL,
  `unit` varchar(25) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_product`
--

LOCK TABLES `tab_product` WRITE;
/*!40000 ALTER TABLE `tab_product` DISABLE KEYS */;
INSERT INTO `tab_product` VALUES ('THI0002','Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá','','','Thùng','Cái',1,1,'2026-06-30 09:29:56',0,'2026-06-30 09:29:56',0),('THC0003','Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen','','','Thùng','Cái',1,2,'2026-06-30 09:29:56',0,'2026-06-30 09:29:56',0),('THC0004','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','','','Thùng','Cái',1,3,'2026-06-30 09:29:56',0,'2026-06-30 09:29:56',0),('NL0001','Nguyên liệu Vi lượng AV4','','','Nguyên liệu','Kg',1,4,'2026-06-30 09:29:56',0,'2026-06-30 09:29:56',0);
/*!40000 ALTER TABLE `tab_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_purchase_order`
--

DROP TABLE IF EXISTS `tab_purchase_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_purchase_order` (
  `code` varchar(50) NOT NULL,
  `misa_code` varchar(50) NOT NULL,
  `pr_code` varchar(50) NOT NULL,
  `survey_code` varchar(50) NOT NULL,
  `company_id` bigint NOT NULL,
  `supplier_code` varchar(50) NOT NULL,
  `supplier_name` varchar(255) NOT NULL,
  `department` varchar(255) NOT NULL,
  `nspt` varchar(100) NOT NULL,
  `order_date` varchar(10) NOT NULL,
  `vat_rate` decimal(5,4) NOT NULL,
  `payment_terms` varchar(255) NOT NULL,
  `is_urgent` tinyint(1) NOT NULL,
  `status` varchar(30) NOT NULL,
  `note` text NOT NULL,
  `approve_note` text NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_purchase_order`
--

LOCK TABLES `tab_purchase_order` WRITE;
/*!40000 ALTER TABLE `tab_purchase_order` DISABLE KEYS */;
INSERT INTO `tab_purchase_order` VALUES ('PO00001','MISA-HD-A','','',27,'XANH VIỆT VINA','CÔNG TY TNHH XANH VIỆT VINA','','','2026-06-01',0.0800,'',0,'partial','','',1,'2026-06-30 09:47:22',1,'2026-06-30 09:47:22',1),('PO00002','MISA-HD-B','','',27,'XANH VIỆT VINA','CÔNG TY TNHH XANH VIỆT VINA','','','2026-06-01',0.0800,'',0,'partial','sua khi da duyet','test',2,'2026-06-30 09:47:22',1,'2026-06-30 10:29:33',1);
/*!40000 ALTER TABLE `tab_purchase_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_purchase_request`
--

DROP TABLE IF EXISTS `tab_purchase_request`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_purchase_request` (
  `code` varchar(50) NOT NULL,
  `company_id` bigint NOT NULL,
  `requester` varchar(255) NOT NULL,
  `requester_position` varchar(100) NOT NULL,
  `department` varchar(255) NOT NULL,
  `head_of_dept` varchar(255) NOT NULL,
  `purpose` varchar(255) NOT NULL,
  `request_date` varchar(10) NOT NULL,
  `need_date` varchar(10) NOT NULL,
  `status` varchar(30) NOT NULL,
  `is_urgent` tinyint(1) NOT NULL,
  `vat_rate` decimal(5,4) NOT NULL,
  `assignee_id` bigint NOT NULL,
  `note` text NOT NULL,
  `show_code_on_print` tinyint(1) NOT NULL,
  `suggested_supplier` varchar(255) NOT NULL,
  `suggested_supplier_tax_code` varchar(50) NOT NULL,
  `suggested_supplier_contact` varchar(255) NOT NULL,
  `quote_filename` varchar(255) NOT NULL,
  `quote_file_url` varchar(1000) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_purchase_request`
--

LOCK TABLES `tab_purchase_request` WRITE;
/*!40000 ALTER TABLE `tab_purchase_request` DISABLE KEYS */;
INSERT INTO `tab_purchase_request` VALUES ('PYC00001',27,'Nguyễn Văn An','Nhân viên KD','Phòng Kinh doanh','Trần Quốc Bảo','Mua bao bì cho lô hàng tháng 7','2026-06-20','2026-07-04','submitted',1,0.0800,0,'NCC báo chạy đơn chai mới phải phối màu nên sẽ giao trễ lịch.',1,'','','','','',1,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('PYC00002',27,'Lê Thị Hoa','Trưởng bộ phận SX','Phòng Sản xuất','Lê Thị Hoa','Bổ sung nguyên liệu vi lượng','2026-06-22','2026-07-10','approved',0,0.0800,0,'',1,'','','','','',2,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),('PYC00003',27,'Phạm Minh Tuấn','Nhân viên mua hàng','Phòng Thu mua','Trần Quốc Bảo','Mua thùng carton đóng gói','2026-06-25','2026-07-15','draft',0,0.0800,0,'',1,'','','','','',3,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1);
/*!40000 ALTER TABLE `tab_purchase_request` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_purchase_request_item`
--

DROP TABLE IF EXISTS `tab_purchase_request_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_purchase_request_item` (
  `pr_id` bigint NOT NULL,
  `product_code` varchar(50) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `item_group` varchar(100) NOT NULL,
  `group_desc` varchar(255) NOT NULL,
  `qty` decimal(18,3) NOT NULL,
  `unit` varchar(25) NOT NULL,
  `price` decimal(18,2) NOT NULL,
  `amount` decimal(18,2) NOT NULL,
  `warehouse` varchar(100) NOT NULL,
  `assignee` varchar(100) NOT NULL,
  `line_status` varchar(30) NOT NULL,
  `progress_note` text NOT NULL,
  `note` varchar(255) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_purchase_request_item_pr_id` (`pr_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_purchase_request_item`
--

LOCK TABLES `tab_purchase_request_item` WRITE;
/*!40000 ALTER TABLE `tab_purchase_request_item` DISABLE KEYS */;
INSERT INTO `tab_purchase_request_item` VALUES (1,'THC0004','Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng','Thùng','',2000.000,'Cái',9000.00,18000000.00,'','','','','',1,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),(1,'THC0003','Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen','Thùng','',2000.000,'Cái',8500.00,17000000.00,'','','','','',2,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),(2,'NL0001','Nguyên liệu Vi lượng AV4','Nguyên liệu','',500.000,'Kg',120000.00,60000000.00,'','','','','',3,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),(3,'THI0002','Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá','Thùng','',1500.000,'Cái',11000.00,16500000.00,'','','','','',4,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1),(3,'THC0003','Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen','Thùng','',800.000,'Cái',8500.00,6800000.00,'','','','','',5,'2026-06-30 07:07:10',1,'2026-06-30 07:07:10',1);
/*!40000 ALTER TABLE `tab_purchase_request_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_role`
--

DROP TABLE IF EXISTS `tab_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_role` (
  `code` varchar(25) NOT NULL,
  `name` varchar(255) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_role`
--

LOCK TABLES `tab_role` WRITE;
/*!40000 ALTER TABLE `tab_role` DISABLE KEYS */;
INSERT INTO `tab_role` VALUES ('admin','Quản trị hệ thống',1,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0);
/*!40000 ALTER TABLE `tab_role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_supplier`
--

DROP TABLE IF EXISTS `tab_supplier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_supplier` (
  `code` varchar(50) NOT NULL,
  `name` varchar(255) NOT NULL,
  `tax_code` varchar(25) NOT NULL,
  `address` text NOT NULL,
  `supplier_type` varchar(20) NOT NULL,
  `payment_terms` varchar(255) NOT NULL,
  `vat` float NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=320 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_supplier`
--

LOCK TABLES `tab_supplier` WRITE;
/*!40000 ALTER TABLE `tab_supplier` DISABLE KEYS */;
INSERT INTO `tab_supplier` VALUES ('Cẩm Hùng','CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI BAO BÌ CẨM HÙNG','1801778241','','goods','Công nợ 60 ngày',0.08,1,1,'2026-06-29 13:45:11',0,'2026-06-29 13:45:11',0),('Đông Tây','CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG TÂY','0316254811','','goods','Công nợ 30 ngày',0.08,1,2,'2026-06-29 13:45:11',0,'2026-06-29 13:45:11',0),('Mộc Ấn','CÔNG TY TNHH QUẢNG CÁO MỘC ẤN','0312214688','','goods','Thanh toán 100% khi nhận hàng',0.1,1,3,'2026-06-29 13:45:11',0,'2026-06-29 13:45:11',0),('Mekong Logistics','Mekong Logistics','','','transport','Công nợ theo chuyến',0.08,1,4,'2026-06-29 13:45:11',0,'2026-06-29 13:45:11',0),('Sang Giàu','Vận chuyển Sang Giàu','','','transport','Tiền mặt',0,1,5,'2026-06-29 13:45:11',0,'2026-06-29 13:45:11',0),('Tân Đức','CÔNG TY TNHH SẢN XUẤT- THƯƠNG MẠI- DỊCH VỤ TÂN ĐỨC','0301909568','108/8 Đường số 11, Khu phố 5, Phường Linh Xuân, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,183,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thành Công','CÔNG TY TRÁCH NHIỆM HỮU HẠN MỘT THÀNH VIÊN HỢP TRÍ THÀNH CÔNG','180135601700','98, đường 3/2, Phường Xuân Khánh, Quận Ninh Kiều, Thành phố Cần Thơ, Việt Nam','goods','',0.08,1,184,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('An Tín','CÔNG TY TNHH SẢN XUẤT - THƯƠNG MẠI AN TÍN','0315259038','247/16 Đường Bình Tiên, Phường 08, Quận 6, Thành Phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,185,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Cường Phát','CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI NHỰA CƯỜNG PHÁT LONG AN','1101721810','Ấp Hóc Thơm 1, Xã Hòa Khánh, Tỉnh Tây Ninh, Việt Nam','goods','',0.08,1,186,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hns','CÔNG TY TNHH BAO BÌ HNS','1801399719','084 QL1, KV2, Ba Láng, Cái Răng, Cần Thơ','goods','',0.08,1,187,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hồ Gia','CÔNG TY TNHH MTV SẢN XUẤT THƯƠNG MẠI NHỰA HỒ GIA','0315743256','100/7B khu phố 1, Bùi Dương Lịch, Phường Bình Hưng Hòa B, Quận Bình Tân, Thành phố Hồ Chí Minh','goods','',0.08,1,188,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Minh Ngọc','CÔNG TY TNHH BAO BÌ MINH NGỌC','0313694927','Lô D2.1 - D2.2 Đường số 4, KCN Nhị Xuân, Xã Xuân Thới Sơn, Huyện Hóc Môn, Tp. HCM','goods','',0.08,1,189,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Quang Đạt','CÔNG TY TNHH SX TM DV  QUỐC TẾ QUANG ĐẠT','0317703989','43D, Ao Đôi, P. Bình Trị Đông A, Q. Bình Tân, TP. HCM','goods','',0.08,1,190,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thành Phát','CÔNG TY CỔ PHẦN BAO BÌ NHỰA THÀNH PHÁT','0302299160','F01-1, đường số 1, KCN Hạnh Phúc, ấp 5 Đức Hoà Đông, ĐH, LA','goods','',0.08,1,191,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Phương Nam','CÔNG TY TNHH BAO BÌ NHỰA PHƯƠNG NAM','0301515210','384A, Tổ 3, Ấp 1, Xã Mỹ Hạnh, Tỉnh Tây Ninh, Việt Nam','goods','',0.08,1,192,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('PHL','CÔNG TY CỔ PHẦN PHL','1101392309','Lô MB1-1, Lô MB1-1a, khu công nghiệp Đức Hòa 1, Đường số 5, Ấp 5, Xã Đức Hòa Đông, Huyện Đức Hoà, Tỉnh Long An, Việt Nam','goods','',0.08,1,193,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Vinaco','CÔNG TY TNHH SẢN XUẤT BAO BÌ VINACO','1101950715','Lô B10, Đường số 1, KCN Hải Sơn (GĐ 3+4), Xã Đức Hòa Hạ, Huyện Đức Hòa, tỉnh Long An','goods','',0.08,1,194,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hải Bình','CÔNG TY TNHH SX TM DV HẢI BÌNH','302202299','30 Võ Hoành, Phường Phú Thọ Hoà, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,195,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hóa Chất Miền Nam','CÔNG TY CP HÓA CHẤT MIỀN NAM','1800662621','137B -137C, Trần Hưng Đạo, Phường An Phú, Quận Ninh Kiều, Thành phố Cần Thơ','goods','',0.08,1,196,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Tmg','CÔNG TY CP QUÔC TẾ TM GROW','3600630513','Trung tâm dịch vụ khu công nghiệp Amata, đường Amata, KCN Amata, Phường Long Bình, Thành phố Biên Hoà, Tỉnh Đồng Nai','goods','',0.08,1,197,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Đắc Khang','CÔNG TY CP ĐẮC KHANG','304714687','482/10/28A1 Nơ Trang Long, Phường 13, Quận Bình Thạnh, Thành phố Hồ Chí Minh','goods','',0.08,1,198,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Phát Đại Lộc','CÔNG TY TNHH SX TM DV PHÁT ĐẠI LỘC','317409056','Số 24 Đường Hiệp Thành 48, Phường Hiệp Thành, Quận 12, Thành phố Hồ Chí Minh','goods','',0.08,1,199,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hiền Phan','CÔNG TY TNHH THƯƠNG MẠI HIỀN PHAN','305877109','Số 64 Lê Lăng, Phường Phú Thọ Hoà, Quận Tân Phú, Thành phố Hồ Chí Minh','goods','',0.08,1,200,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Vạn An','CÔNG TY TNHH XNK HÓA CHẤT VẠN AN','314845752','208C Nguyễn Ngọc Nhựt, Phường Tân Quý, Quận Tân Phú, Thành phố Hồ Chí Minh','goods','',0.08,1,201,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Vĩnh Nam Anh','CÔNG TY TNHH VĨNH NAM ANH','304973949','65/1 Ấp 1, Bùi Công Trừng, Xã Nhị Bình, Huyện Hóc Môn, Thành phố Hồ Chí Minh','goods','',0.08,1,202,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hòa Phát','CÔNG TY TNHH KỸ THUẬT AN TOÀN MÔI TRƯỜNG HÒA PHÁT','312483507','173/53 Thoại Ngọc Hầu, Phường Phú Thạnh, Quận Tân Phú, Thành phố Hồ Chí Minh','goods','',0.08,1,203,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Mekong','CÔNG TY TNHH NGUYÊN LIỆU NÔNG NGHIỆP MEKONG','313587019','Lô Officetel L4-20, tầng 20, Block Lucky, Tòa nhà Richmond City, 207C Nguyễn Xí, Phường Bình Thạnh, TP. Hồ Chí Minh','goods','',0.08,1,204,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('An Gia Phú','CÔNG TY TNHH SX VÀ TM AN GIA PHÚ','313155900','40/17/9 Đường số 7, Khu phố 12, Phường Bình Hưng Hòa, Quận Bình Tân, Thành phố Hồ Chí Minh','goods','',0.08,1,205,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Ngàn Hương','CÔNG TY TNHH XNK NGÀN HƯƠNG','1800385992','133K, Trần Hưng Đạo, Phường An Phú, Quận Ninh Kiều, Thành phố Cần Thơ','goods','',0.08,1,206,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Mạnh Đan','CÔNG TY CỔ PHẦN MẠNH ĐAN','311118396','43 Đường số 5, Cư xá Chu Văn An, Phường 26, Quận Bình Thạnh, Thành phố Hồ Chí Minh','goods','',0.08,1,207,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Trung Phong','CÔNG TY TNHH VẬT TƯ NÔNG NGHIỆP TRUNG PHONG','314509888','36/7 Lam Sơn , Phường 6, Quận Bình Thạnh, Thành phố Hồ Chí Minh','goods','',0.08,1,208,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Jd','CÔNG TY TNHH SOLUTION JD','0314465052','43 đường số 5, cư xá Chu Văn An , Phường 26, Quận Bình Thạnh, Thành phố Hồ Chí Minh','goods','',0.08,1,209,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kel','CÔNG TY TNHH KING ELONG','0317197235','Lô Officetel L5-20, Tầng 20, Block Lucky, Tòa nhà Richmond City, 207C Nguyễn Xí, Phường 26, Quận Bình Thạnh, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,210,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Ntk','CÔNG TY TNHH HOÁ SINH NTK','1102004566','Lô B113, đường số 5, KCN Thái Hoà, Xã Đức Lập Hạ, Huyện Đức Hoà, Tỉnh Long An','goods','',0.08,1,211,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Mộc Lan','CÔNG TY TNHH CÂY XANH MỘC LAN','3603725410','Số 112/8/2 Tổ 8, khu phố Tân Cang, phường Phước Tân, TP Biên Hòa, tỉnh Đồng Nai','goods','',0.08,1,212,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Nam Bình','CÔNG TY TNHH THƯƠNG MẠI HÓA CHẤT NAM BÌNH','0309910935','4/107, Ấp Nhị Tân 2, Xã Tân Thới Nhì, Huyện Hóc Môn, Thành phố Hồ Chí Minh','goods','',0.08,1,213,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kết Nông','CÔNG TY TNHH XNK KẾT NÔNG','0315006943','119/83 Nguyễn Thị Tần, Phường 2, Quận 8, TP HCM','goods','',0.08,1,214,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hóa Chất Mê Kông','CÔNG TY TNHH HÓA CHẤT MÊ KÔNG','0304920055','74A Đường số 18, Phường 8, Quận Gò Vấp, TP.HCM, Việt Nam','goods','',0.08,1,215,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Đệ Nhất','CÔNG TY CỔ PHẦN THIẾT BỊ ĐỆ NHẤT','0310937272','Tầng 3, Phòng 3.07, khu I, Tòa nhà The Prince Residence, số 19-21 Nguyễn Văn Trỗi, Phường 11, Quận Phú Nhuận, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,216,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Svc','CÔNG TY TNHH SVC CHEMICAL','1101987225','Số nhà C17, đường số 4, KDC Trần Anh, Ấp Mới 2, Xã Mỹ Hạnh Nam, Huyện Đức Hòa, Tình Long An','goods','',0.08,1,217,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Khả Doanh','CÔNG TY TNHH KHẢ DOANH','303557142','9/27 Phạm Văn Hai, Phường 1, Quận Tân Bình, TP Hồ Chí Minh','goods','',0.08,1,218,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Basel Thụy Sĩ','CÔNG TY TNHH BASEL THỤY SĨ','1101742391','Lô H2A đường số 4, KCN Hải Sơn (GĐ 3+4), ấp Bình Tiền 2, Xã Đức Hòa Hạ, Huyện Đức Hoà, Tỉnh Long An','goods','',0.08,1,219,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thiên Nhiên Xanh','CÔNG TY TNHH DƯỢC LIỆU THIÊN NHIÊN XANH','314051566','85A Ỷ Lan, Phường Hiệp Tân, Quận Tân Phú, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,220,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thịnh Phát Vi Na','CÔNG TY TNHH THỊNH PHÁT VI NA','303702463','110 Đường số 30, Phường An Lạc, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,221,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Nguyễn Bá','CÔNG TY TNHH SẢN XUẤT VÀ THƯƠNG MẠI NGUYỄN BÁ','308923441','10-12 Trung Lang, Phường Bảy Hiền, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,222,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thuận Duyên','CÔNG TY CỔ PHẦN XUẤT NHẬP KHẨU THƯƠNG MẠI SẢN XUẤT HÓA CHẤT THUẬN DUYÊN','311269934','49/6G Bà Điểm 11, Ấp Đông Lân, Xã Bà Điểm, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,223,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Việt Mỹ','CÔNG TY CỔ PHẦN VIỆT MỸ CẦN THƠ','1801548985','M40- đường 3A- KDC Hưng Phú 1- Quận Cái Răng- TP.Cần Thơ','goods','',0.08,1,224,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Châu Ngân','CÔNG TY CỔ PHẦN XUẤT NHẬP KHẨU CHÂU NGÂN','309818111','71 Đường Số 27, KDC Tân Quy Đông, Phường Tân Hưng, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,225,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('An Khánh','CÔNG TY TNHH THIẾT BỊ - HÓA CHẤT KHOA HỌC KỸ THUẬT AN KHÁNH','1800702458','43, đường 14, Khu tái định cư Thới Nhựt, Phường Tân An, TP Cần Thơ, Việt Nam','goods','',0.08,1,226,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Nutifer Vn','CÔNG TY TNHH NUTIFER VN','1101793371','Lô D01A, CCN Đức Thuận, KCN Đức Hoà 3, Ấp Tràm Lạc, Xã Đức Lập, Tỉnh Tây Ninh, Việt Nam','goods','',0.08,1,227,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hiền Phan Long An','CÔNG TY TNHH TM HIỀN PHAN LONG AN','1102007045','Lô A5.1, Đường số 1, KCN Đức Hòa III - Tập Đoàn Tân Á Đại Thành, Ấp Đức Hạnh 2, Xã Đức Lập, Tỉnh Tây Ninh, Việt Nam','goods','',0.08,1,228,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Cvgr','CÔNG TY CỔ PHẦN CVGREEN','0316184314','14/4 Thạnh Xuân 18, Phường Thới An, Thành Phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,229,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Namsiang','CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ NAMSIANG VIỆT NAM','310194210','180/21 Lý Thánh Tông, Phường Phú Thạnh, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,230,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Nam Hà','CÔNG TY TNHH NAM HÀ','1800567865','103 Lý Tự Trọng, Phường Ninh Kiều, Thành phố Cần Thơ','goods','',0.08,1,231,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kỳ Anh','CÔNG TY TNHH SẢN XUẤT VÀ THƯƠNG MẠI DƯỢC LIỆU KỲ ANH','1402129830','Ấp Mỹ Hòa 1, Xã Tháp Mười, Tỉnh Đồng Tháp, Việt Nam','goods','',0.08,1,232,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Trương Gia Phước','CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ IN ẤN TRƯƠNG GIA PHƯỚC','1801514778','Số 311 Nguyễn Văn Cừ, Phường Cái Khế, Thành phố Cần Thơ, Việt Nam','goods','',0.08,1,233,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Như Cương','DOANH NGHIỆP TƯ NHÂN NHƯ CƯƠNG','1800525914','78, đường 30/4, phường Ninh Kiều, TP Cần Thơ','goods','',0.08,1,234,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Tân Hoa Mai','CÔNG TY TNHH IN ẤN KỸ THUẬT MỚI TÂN HOA MAI','0311275254','96/5A Đặng Thùy Trâm, Phường Bình Lợi Trung, Thành Phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,235,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Cbv','HỢP TÁC XÃ SẢN XUẤT THƯƠNG MẠI NÔNG, THỦY SẢN CÁNH BUỒM VÀNG','315907352','B14/257 Ấp 2, xã Tân Nhựt, huyện Bình Chánh, TP. Hồ Chí Minh','goods','',0.08,1,236,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Ldb','CÔNG TY TNHH TMDV LADYBUG VIỆT NAM','317370225','32/36/27 Ông Ích Khiêm, Phường 14, Quận 11, TP Hồ Chí Minh','goods','',0.08,1,237,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Cmc','CÔNG TY TNHH CEMACO VIỆT NAM','0108075628005','87B1 Ung Văn Khiêm, P. Cái Khế, Q. Ninh Kiều, Thành phố Cần Thơ, Việt Nam','goods','',0.08,1,238,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Aq','CÔNG TY CP CÔNG NGHỆ AQUADELTA','1801666202','55 đường 3/2, phường Hưng lợi, quận Ninh Kiều, TPCT','goods','',0.08,1,239,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Du Bai','CÔNG TY TNHH HÓA CHẤT PHÂN BÓN, THUỐC BVTV DUBAI','1101798524','Lô B115, Đường số 5, KCN Thái Hòa, Ấp Tân Hòa, Xã Đức Lập Hạ, Huyện Đức Hòa, Tỉnh Long An','goods','',0.08,1,240,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Gemachem','CÔNG TY CỔ PHẦN GEMACHEM VIỆT NAM','102135197','46 Ngồ Quyền, P Hàng Bài, Quận Hoàn Kiếm, TP Hà Nội','goods','',0.08,1,241,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Gemsky','CÔNG TY TNHHH THƯƠNG MẠI GEMSKY','316840661','507 Lũy Bán Bích, Phường Phú Thạnh,  TP HCM','goods','',0.08,1,242,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('An Phát','CÔNG TY CỔ PHẦN THIẾT BỊ KIỂM ĐỊNH AN PHÁT','108673258','Km số 9, đường 72, xã Cộng Hòa, huyện Quốc Oai, thành phố Hà Nội.','goods','',0.08,1,243,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Phương Lâm','Cửa Hàng Phương Lâm','','Ngõ 2 đội 3 Võng La - Đông Anh - Hà Nội','goods','',0.08,1,244,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Khai Nhật','CÔNG TY TNHH KHAI NHẬT','0317473485','Tầng 15, P.1508 Tòa nhà Vincom Center, Số 72 Lê Thánh Tôn, Phường Bến Nghé, Quận 1, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,245,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Sam Chem','CÔNG TY CP SAM CHEM QUẢ CẦU','0304750798','Lầu 7, Số 82 Trần Huy Liệu - Phường 15 - Quận Phú Nhuận - TP HCM','goods','',0.08,1,246,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thùy Anh','CÔNG TY CP ĐẦU TƯ PHÁT TRIỂN THƯƠNG MẠI VÀ DỊCH VỤ THÙY ANH','0109206922','Thửa đất số 1, khu đất dịch vụ thôn Yên Vĩnh, xã Kim Chung, huyện Hoài Đức, TP Hà Nội33/4F','goods','',0.08,1,247,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hkm','CÔNG TY TNHH THIẾT BỊ KHOA HỌC CÔNG NGHỆ HKM','0312965740','52/4T Đường Xuân Thới 3, Ấp Xuân Thới Đông 2, Xã Xuân Thới Đông, Huyện Hóc Môn, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,248,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Mỹ Kỳ','CÔNG TY TNHH CÔNG NGHIỆP MỸ KỲ','0313245382','87/1 Đường TL 41, Phường An Phú Đông, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,249,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Sài Gòn Nguyễn','CÔNG TY TNHH ĐẦU TƯ THƯƠNG MẠI SÀI GÒN NGUYỄN','0314511301','30/12/18 Đường 49, Phường Hiệp Bình, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,250,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Intrie','CÔNG TY TNHH INTRIE','0317214025','56/16 Nguyễn Văn Săng, Phường Tân Sơn Nhì, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,251,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kpos','CÔNG TY TNHH MỘT THÀNH VIÊN TM AN KHÁNH','0316113105','623 Tên Lửa, Phường An Lạc, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,252,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hdsd Antisol','CÔNG TY TNHH WAF BRANDS','1801773973','72/1 Nguyễn Trãi, Phường Ninh Kiều, Thành phố Cần Thơ, Việt Nam','goods','',0.08,1,253,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Trí Tín','CÔNG TY TNHH IN BAO BÌ TRÍ TÍN','0311841439','168/59A Đường Bình Trị Đông, Phường Bình Trị Đông, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,254,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Sáng Tâm','CÔNG TY TNHH SẢN XUẤT BAO BÌ NHỰA SÁNG TÂM','0317140831','841 Quốc Lộ 1A, Phường Bình Hưng Hòa, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,255,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thiên An Phú','CÔNG TY TRÁCH NHIỆM HỮU HẠN SẢN XUẤT THƯƠNG MẠI THIÊN AN PHÚ','0314862758','1A140 Vĩnh Lộc, Xã Phạm Văn Hai, Huyện Bình Chánh, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,256,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Oanh Design','CÔNG TY TNHH MỸ THUẬT ỨNG DỤNG MASTER','317050521','240/32 Nguyễn Văn Luông, Phường Bình Phú, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,257,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hiệp Phát','CÔNG TY TNHH XNK HIỆP PHÁT CHEM','1101925116','Lô Q17A-18 đường số 11, KCN Hải Sơn mở rộng (GĐ 3+4), Xã Đức Hòa , Tỉnh Tây Ninh, Việt Nam','goods','',0.08,1,258,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('AMG','CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ AMG GROUP','108764547','Số 63 Vũ Ngọc Phan, phường Láng Hạ, quận Đống Đa, Hà Nội','goods','',0.08,1,259,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('VNT','CÔNG TY CỔ PHẦN THƯƠNG MẠI XUẤT NHẬP KHẨU VNT','0104188003','Xóm 3, Thôn Hải Bối, Xã Vĩnh Thanh, Thành phố Hà Nội, Việt Nam','goods','',0.08,1,260,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Short Hills','CÔNG TY TNHH SHORT HILLS VIỆT NAM','318537734','Tầng 6, Toà nhà Intan, số 97 Nguyễn Văn Trỗi, Phường Phú Nhuận, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,261,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hải Đăng','CÔNG TY CỔ PHẦN XNK HÓA CHẤT HẢI ĐĂNG','5702087191','Tổ 41, Khu 4, Hà Khẩu, Tp Hạ Long, Tỉnh Quảng Ninh','goods','',0.08,1,262,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hà Linh','CÔNG TY TNHH PHÂN BÓN HÓA CHẤT HÀ LINH','1501146107','Thửa đất số 861, tờ bản đồ số 9, tổ 10, ấp Mỹ Hưng 2, Phường Cái Vồn, Tỉnh Vĩnh Long, Việt Nam','goods','',0.08,1,263,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('La Hán Hoàng Phát','CÔNG TY CỔ PHẦN LA HÁN HOÀNG PHÁT','108529582','Số nhà 83D, Ngõ 165 Dương Quảng Hàm, Phường Quan Hoa, Quận Cầu Giấy, TP Hà Nội','goods','',0.08,1,264,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Phát Thiên Phú','CÔNG TY TNHH PHÁT THIÊN PHÚ','3600889932','Số 38-40-42, đường N18, khu Phố Vinh Thạnh, Phường Trấn Biên, Tỉnh Đồng Nai, Việt Nam','goods','',0.08,1,265,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Alley 70','CÔNG TY CỔ PHẦN ALLEY 70','317962278','70/17D Đinh Bộ Lĩnh, Phường 26, Quận Bình Thạnh, Thành phố Hồ Chí Minh','goods','',0.08,1,266,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Quang Trung','CÔNG TY TNHH SX TM QUANG TRUNG','317065768','Thửa 290 tờ bản đồ số 28, KCN Xuyên Á, Đức Hòa, Long An','goods','',0.08,1,267,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('AP Têchm','CÔNG TY TNHH KỸ THUẬT HOÁ PHẨM AP','319161467','Tầng 3, Tòa nhà An Phú Plaza, 117-119 Lý Chính Thắng, Phường Xuân Hòa, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,268,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Ngọc Minh','CÔNG TY TNHH SX TM BAO BÌ NGỌC MINH','313635470','B4 ẤP MỸ HOÀ 4, XUÂN THỚI ĐÔNG, HÓC MÔN, TP.HCM','goods','',0.08,1,269,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Lưu Xuân Giang','CÔNG TY TNHH MỘT THÀNH VIÊN LƯU XUÂN GIANG','1800690555','56A Phạm Ngũ Lão, Phường Cái Khế, TP. Cần Thơ','goods','',0.08,1,270,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('In Tổng Hợp Cần Thơ','CÔNG TY CỔ PHẦN IN TỔNG HỢP CẦN THƠ','1800157925','Số 500 đường 30/4, Phường Tân An, TP. Cần Thơ','goods','',0.08,1,271,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('G28','CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI G28','1101926825','ô LE5, Đường Số 2, KCN Xuyên Á, Xã Đức Lập, Tỉnh Tây Ninh, Việt Nam \n XSX: 31/13 Ấp 4, Đường Dương Công Khi, Xã Xuân Thới Sơn, TP. Hồ Chí Minh.','goods','',0.08,1,272,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Bao Bì Đông Bắc','CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG BẮC','318450547','Số 11 Đường 406 Ấp 2, Xã Củ Chi, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,273,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Bao Bì Duy Nhật','Công ty TNHH SX & TM Duy Nhật','2200717750','Lô O, KCN An Nghiệp, Xã An Nghiệp, Tỉnh Vĩnh Long','goods','',0.08,1,274,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Dao Carton','CTY TNHH SX TM DV TH DAO CARTON','1801699046','Số 83, Đường B13, KDC 91B, Phường Tân An, Thành phố Cần Thơ, Việt Nam','goods','',0.08,1,275,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Bao Bì Giấy An Tín','CÔNG TY TNHH BAO BÌ GIẤY AN TÍN','0315839173','Số 23 Đường 23, Khu phố 2, Phường Tam Bình, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,276,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Bao Bì Trọng Tín','CÔNG TY CỔ PHẦN BAO BÌ TRỌNG TÍN','0313183129','Số 112/7 Đường Lê Thị Hà, Tổ 11, Ấp Chánh 1, Xã Hóc Môn, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,277,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Giấy Yuen Foong Yu','CÔNG TY TNHH GIẤY YUEN FOONG YU (VN)','1100635534','Lô E3, E4, E5, E6 khu công nghiệp Đức Hòa 1, Ấp 5, Xã Mỹ Hạnh, Tỉnh Tây Ninh, Việt Nam','goods','',0.08,1,278,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hebei Veyong','HEBEI VEYONG BIO-CHEMICAL CO., LTD.','','NO.6, MIDDLE HUAGONG ROAD, CIRCULATION CHEMICAL\nINDUSTRY PARK, SHIJIAZHUANG CITY, HEBEI, CHINA','goods','',0.08,1,279,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Tien Yuan','TIEN YUAN CHEMICAL (PTE) LTD.','','NO. 18 CHIN BEE ROAD, JURONG TOWN, SINGAPORE 619827','goods','',0.08,1,280,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hoa Việt Chemgroup','CÔNG TY TNHH HOA VIỆT CHEMGROUP','0317598043','A2/11Y, tổ 3, ấp 1, xã Vĩnh Lộc A, huyện Bình Chánh, TP.HCM','goods','',0.08,1,281,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Nông Nghiệp Thông Minh','CÔNG TY TNHH ĐẦU TƯ NÔNG NGHIỆP THÔNG MINH','0312170342','33 Đường 2, Phường Phước Long, Thành phố Hồ Chí Minh, Việt Nam;','goods','',0.08,1,282,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Trần Tiến','CÔNG TY TNHH XUẤT NHẬP KHẨU TRẦN TIẾN','0312284043','911-913-915-917 Nguyễn Trãi, Phường Chợ Lớn, Tp. Hồ Chí Minh','goods','',0.08,1,283,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Việt Mỹ (Sài Gòn)','CÔNG TY CỔ PHẦN XUẤT NHẬP KHẨU HÓA CHẤT VIỆT MỸ','0312669004','9 Đường số 5, Bình Hưng, Bình Chánh, TP.HCM','goods','',0.08,1,284,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Ak Vina','CÔNG TY TRÁCH NHIỆM HỮU HẠN AK VINA AK VINA CO., LTD','3600649634','Số 02, KCN Gò Dầu, Xã Phước Thái, Huyện Long Thành, Tỉnh Đồng Nai, Việt Nam','goods','',0.08,1,285,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Amigos','CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI AMIGOS','0311360340','60/15 Huỳnh Văn Nghệ, Phường Tân Sơn, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,286,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('MIA','CÔNG TY TNHH VẬT TƯ NÔNG NGHIỆP MIA','0315662254','12/29 Nguyễn Tuân, Phường Hạnh Thông, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,287,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Agama','CÔNG TY CỔ PHẦN AGAMA','','Lô 2, Đường số 2, Cụm Công nghiệp Đức Thuận, Ấp Tràm Lạc, Xã Mỹ Hạnh Bắc, Huyện Đức Hoà, Tỉnh Long An, Việt Nam','goods','',0.08,1,288,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Hà Long','CÔNG TY CỔ PHẦN HÓA CHẤT NÔNG NGHIỆP HÀ LONG','','Lô A 204, Khu công nghiệp Thái Hòa , Xã Đức Lập Hạ, Huyện Đức Hoà, Tỉnh Long An, Việt Nam','goods','',0.08,1,289,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Âu Việt','CÔNG TY CỔ PHẦN PHÂN BÓN QUỐC TẾ ÂU VIỆT (CÔNG TY CP EVF)','','Quốc lộ 1A, Ấp Long An B, Thị Trấn Cái Tắc, Huyện Châu Thành A, Tỉnh Hậu Giang, Việt Nam','goods','',0.08,1,290,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Basel','CÔNG TY TNHH BASEL THỤY SĨ','','Lô H2A đường số 4, KCN Hải Sơn (GĐ 3+4), ấp Bình Tiền 2, Xã Đức Hòa Hạ, Huyện Đức Hoà, Tỉnh Long An','goods','',0.08,1,291,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Dego Cần Thơ','CÔNG TY TNHH DEGO HOLDING','','B19 đường cầu dẫn cầu Cần Thơ, QL 1A, Khu Dân cư Trung tâm văn hóa Tây Đô, phường Cái Răng, Thành phố Cần Thơ.','goods','',0.08,1,292,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Niềm Tin Việt','CÔNG TY TNHH PHÂN BÓN NIỀM TIN VIỆT','','Ấp 2A, Xã Hưng Thạnh, H.Tháp Mười, Đồng Tháp','goods','',0.08,1,293,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Đại Tâm','CÔNG TY TNHH PRIMA - PHÁP - CHÂU ÂU','','Lô B101 đường B. KCN Thái Hoà, Xã Đức Lập Hạ, Huyện Đức Hoà, Tỉnh Long An','goods','',0.08,1,294,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Pesticidex','CÔNG TY TNHH SÀN GIAO DỊCH THUỐC BẢO VỆ THỰC VẬT VIỆT NAM','','Tầng 1, B19 đường dẫn cầu Cần Thơ, Quốc lộ 1A, KDC TTVH Tây Đô, Phường Hưng Thạnh, Quận Cái Răng, Thành phố Cần Thơ, Việt Nam','goods','',0.08,1,295,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Yamato','CÔNG TY TNHH SX TM YAMATO VN','','Lô A20A Đường số 6, KCN Hải Sơn (GĐ 3+4), Xã Đức Hòa Hạ, Huyện Đức Hoà, Tỉnh Long An','goods','',0.08,1,296,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('ATC','CÔNG TY TNHH XUẤT NHẬP KHẨU HÓA CHẤT ATC','','Số 87, Đường Lý Bôn, Phường Bình Đức, Tỉnh An Giang, Việt Nam','goods','',0.08,1,297,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Agrifuture','CÔNG TY TNHH AGRIFUTURE','','Nhà Máy: Lô B123B, Đường số 7, KCN, ấp Tân Hòa, Đức Hòa, Long An\nVP: Phòng A4.04, Khu Phức Hợp Căn Hộ Nhật Hoa, 33 Nguyễn Hữu Thọ, Phường Tân Hưng, Thành phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,298,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thu Loan','Cty TNHH SX TM DV Thu Loan','','699 tổ 34 Khóm Đông Thuận , Phường Đông Thành , Bình Minh, Vĩnh Long','goods','',0.08,1,299,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Thái Nông','CÔNG TY TNHH THƯƠNG MẠI THÁI NÔNG','','73 Lạc Long Quân, Phường 1, Quận 11, Thành phố Hồ Chí Minh\n CN: Khu Công nghiệp Nhơn Trạch 3, Thị trấn Hiệp Phước, Huyện Nhơn Trạch, Tỉnh Đồng Nai, Việt Nam\n Giao Vật Tư: HKD Cơ Sở Phân Bón Lá Phú Hưng\n ĐC: 49A, đường số 27, Tân Lập, Tân Thông Hội, Củ Chi, HCM\n Người nhận: 0937 021 818 - Chị Bội','goods','',0.08,1,300,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('An Nông','CÔNG TY TNHH TẬP ĐOÀN AN NÔNG (AN GROUP)','','Trụ sở : 464 Đường số 7, khu phố 8, Phường Tân Tạo, Quận Bình Tân, TP Hồ Chí Minh\n Nhà máy : Lô H7, Đường số 5, KCN Hải Sơn (GĐ 3+4), ấp Bình Tiền 2, Xã Đức Hòa Hạ, Huyện Đức Hoà, Tỉnh Long An, Việt Nam','goods','',0.08,1,301,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kho Dr. Xanh','KHO DR XANH','','Số 124 Võ Văn Kiệt, KV Bình Trung, P.Long Hòa, Q. Bình Thủy, Cần Thơ','goods','',0.08,1,302,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kho B18','KHO B18','','B18 đường dẫn cầu Cần Thơ, Quốc lộ 1A, KDC TTVH Tây Đô, Phường Cái Răng, Thành phố Cần Thơ','goods','',0.08,1,303,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kho C1-2','Kho C1-2','','Kho C1-2','goods','',0.08,1,304,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kho F49 - Icare','KHO F49 - ICARE','','nhà F49 (chạy qua trường lái Chiến Thắng) đường số 7, KDC Long Thịnh, Phường Phú Thứ, Cái Răng, Cần Thơ','goods','',0.08,1,305,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Kho Lab Dego','KHO LAB DEGO','','B19 đường dẫn cầu Cần Thơ, Quốc lộ 1A, KDC TTVH Tây Đô, Phường Cái Răng, Thành phố Cần Thơ','goods','',0.08,1,306,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('BAO BÌ LỘC PHÁT','CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ BAO BÌ LỘC PHÁT','1801722746','229 Nguyễn Thị Minh Khai, Ninh Kiều, Cần Thơ','goods','',0.08,1,307,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('CHẤN HƯNG NÔNG','CÔNG TY TNHH CHẤN HƯNG NÔNG','1801800440','Ấp Trường Thọ, Xã Trường Xuân, TP Cần Thơ, Việt Nam.','goods','',0.08,1,308,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('BAO BÌ CHÂU DUY','BAO BÌ CHÂU DUY','','26-28 Ngô Sĩ Liên KDC MeTro,Tân An, Cần Thơ','goods','',0.08,1,309,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('HÓA CHẤT TOÀN CẦU','CÔNG TY TNHH MÁY VÀ HÓA CHẤT TOÀN CẦU','0105111638','Tầng 6, tòa nhà CDS, Số 33,Ngõ 61 Lạc Trung, Phường Vĩnh Tuy, Hà Nội','goods','',0.08,1,310,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('CAO VẠN THỊNH','CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI CAO VẠN THỊNH','0311953982','1004/12 Hương lộ 2, khu phố 6, Phường Bình Trị Đông, TP Hồ Chí Minh, Việt Nam','goods','',0.08,1,311,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('NGỌC HÂN XUYÊN Á','CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ NGỌC HÂN XUYÊN Á','1102106818','Số 134 đường Giồng Lớn, ấp Giồng Lớn, Xã Mỹ Hạnh, Tỉnh Tây Ninh, Việt Nam','goods','',0.08,1,312,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('TANK LÊ HỮU THÔNG','LÊ HỮU THÔNG','079082006587','252 Ấp 17, xã Hiệp Phước, Thành phố Hồ Chí Minh','goods','',0.08,1,313,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Nông Xanh','Công Ty TNHH TM Nông Xanh','0310187076','168 Đường 16, KDC Đông Tăng Long ,P long phước,TP.HCM','goods','',0.08,1,314,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('XANH VIỆT VINA','CÔNG TY TNHH XANH VIỆT VINA','0318499006','Tầng 2, Hado Airport Building, số 2 đường Hồng Hà, Phường Tân Sơn Hòa, Thành Phố Hồ Chí Minh, Việt Nam','goods','',0.08,1,315,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Trần Quyên','Trần Quyên','','','transport','',0.08,1,316,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Phan Khánh','Phan Khánh','','','transport','',0.08,1,317,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('NCC tự vận chuyển','NCC tự vận chuyển','','','transport','',0.08,1,318,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0),('Grab','Grab','','','transport','',0.08,1,319,'2026-06-30 03:01:07',0,'2026-06-30 03:01:07',0);
/*!40000 ALTER TABLE `tab_supplier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_survey`
--

DROP TABLE IF EXISTS `tab_survey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_survey` (
  `code` varchar(50) NOT NULL,
  `survey_type` varchar(10) NOT NULL,
  `pr_code` varchar(50) NOT NULL,
  `received_date` varchar(10) NOT NULL,
  `result_due_date` varchar(10) NOT NULL,
  `item_group` varchar(100) NOT NULL,
  `requirement_detail` text NOT NULL,
  `request_qty` decimal(18,3) NOT NULL,
  `market_price` decimal(18,2) NOT NULL,
  `nspt` varchar(100) NOT NULL,
  `approve_status` varchar(20) NOT NULL,
  `approve_note` text NOT NULL,
  `status` varchar(30) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_survey`
--

LOCK TABLES `tab_survey` WRITE;
/*!40000 ALTER TABLE `tab_survey` DISABLE KEYS */;
INSERT INTO `tab_survey` VALUES ('KS00001','supplier','','2026-06-10','2026-06-18','Bao bì','Khảo sát NCC bao bì thùng carton',1000.000,11000.00,'Nguyễn Văn A','','','submitted',1,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),('KS00002','product','','2026-06-11','2026-06-19','Bao bì','Khảo sát giá sản phẩm thùng',500.000,10500.00,'Trần Thị B','','','draft',2,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1);
/*!40000 ALTER TABLE `tab_survey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_survey_product_line`
--

DROP TABLE IF EXISTS `tab_survey_product_line`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_survey_product_line` (
  `survey_id` bigint NOT NULL,
  `supplier_code` varchar(50) NOT NULL,
  `internal_code` varchar(50) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `spec` text NOT NULL,
  `origin` varchar(100) NOT NULL,
  `quote_unit` varchar(25) NOT NULL,
  `moq` decimal(18,3) NOT NULL,
  `price_by_volume` decimal(18,2) NOT NULL,
  `volume_range` varchar(100) NOT NULL,
  `vat` decimal(5,2) NOT NULL,
  `request_qty` decimal(18,3) NOT NULL,
  `amount` decimal(18,2) NOT NULL,
  `internal_unit` varchar(25) NOT NULL,
  `amount_converted` decimal(18,2) NOT NULL,
  `shipping_cost` decimal(18,2) NOT NULL,
  `delivery_time` varchar(100) NOT NULL,
  `delivery_place` varchar(255) NOT NULL,
  `quote_file` varchar(500) NOT NULL,
  `sample_ready` tinyint(1) NOT NULL,
  `sample_date` varchar(10) NOT NULL,
  `sample_qty` decimal(18,3) NOT NULL,
  `lab_result` varchar(20) NOT NULL,
  `lab_note` text NOT NULL,
  `nspt_note` varchar(20) NOT NULL,
  `nspt_reason` text NOT NULL,
  `line_approve` varchar(20) NOT NULL,
  `line_approve_note` text NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_survey_product_line_survey_id` (`survey_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_survey_product_line`
--

LOCK TABLES `tab_survey_product_line` WRITE;
/*!40000 ALTER TABLE `tab_survey_product_line` DISABLE KEYS */;
INSERT INTO `tab_survey_product_line` VALUES (2,'XANH VIỆT VINA','THC0003','Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen','','','Cái',0.000,10000.00,'',8.00,500.000,5400000.00,'',5400000.00,0.00,'','','',1,'',0.000,'Đạt','','Đạt','','Duyệt','',1,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),(2,'Nông Xanh','THC0003','Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen','','','Cái',0.000,9800.00,'',8.00,500.000,5292000.00,'',5292000.00,0.00,'','','',1,'',0.000,'Đạt','','Đạt','','Duyệt','',2,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1);
/*!40000 ALTER TABLE `tab_survey_product_line` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_survey_supplier_line`
--

DROP TABLE IF EXISTS `tab_survey_supplier_line`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_survey_supplier_line` (
  `survey_id` bigint NOT NULL,
  `contact_date` varchar(10) NOT NULL,
  `reply_date` varchar(10) NOT NULL,
  `result_date` varchar(10) NOT NULL,
  `supplier_code` varchar(50) NOT NULL,
  `supplier_name` varchar(255) NOT NULL,
  `tax_code` varchar(25) NOT NULL,
  `reg_address` text NOT NULL,
  `warehouse_address` text NOT NULL,
  `google_maps` varchar(500) NOT NULL,
  `contact_person` varchar(100) NOT NULL,
  `contact_phone` varchar(30) NOT NULL,
  `supply_group` varchar(255) NOT NULL,
  `quote_folder` varchar(500) NOT NULL,
  `production_tech` varchar(255) NOT NULL,
  `production_time` varchar(100) NOT NULL,
  `nvkd_eval` varchar(100) NOT NULL,
  `invoice_policy` varchar(255) NOT NULL,
  `reliability` varchar(20) NOT NULL,
  `delivery_policy` varchar(255) NOT NULL,
  `debt_policy` varchar(50) NOT NULL,
  `defect_return` varchar(255) NOT NULL,
  `nspt_note` varchar(20) NOT NULL,
  `nspt_reason` text NOT NULL,
  `line_approve` varchar(20) NOT NULL,
  `line_approve_note` text NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_survey_supplier_line_survey_id` (`survey_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_survey_supplier_line`
--

LOCK TABLES `tab_survey_supplier_line` WRITE;
/*!40000 ALTER TABLE `tab_survey_supplier_line` DISABLE KEYS */;
INSERT INTO `tab_survey_supplier_line` VALUES (1,'','','','XANH VIỆT VINA','CÔNG TY TNHH XANH VIỆT VINA','0318499006','','','','NV Kinh doanh','090000000','','','','','','','Cao','','','','Đạt','','Duyệt','',1,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1),(1,'','','','Nông Xanh','Công Ty TNHH TM Nông Xanh','0310187076','','','','NV Kinh doanh','090000000','','','','','','','Cao','','','','Không đạt','Giá cao','Không duyệt','',2,'2026-06-30 06:58:33',1,'2026-06-30 06:58:33',1);
/*!40000 ALTER TABLE `tab_survey_supplier_line` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_unit`
--

DROP TABLE IF EXISTS `tab_unit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_unit` (
  `code` varchar(25) NOT NULL,
  `name` varchar(100) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_unit`
--

LOCK TABLES `tab_unit` WRITE;
/*!40000 ALTER TABLE `tab_unit` DISABLE KEYS */;
INSERT INTO `tab_unit` VALUES ('Cái','Cái',1,1,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Bộ','Bộ',1,2,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Kg','Kg',1,3,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Lít','Lít',1,4,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('ML','ML',1,5,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Gram','Gram',1,6,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Cuộn','Cuộn',1,7,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Bịch','Bịch',1,8,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Cây','Cây',1,9,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Thùng','Thùng',1,10,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Hộp','Hộp',1,11,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0);
/*!40000 ALTER TABLE `tab_unit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_user`
--

DROP TABLE IF EXISTS `tab_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_user` (
  `email` varchar(255) NOT NULL,
  `google_sub` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `employee_id` bigint NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_user_employee_id` (`employee_id`),
  KEY `ix_tab_user_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_user`
--

LOCK TABLES `tab_user` WRITE;
/*!40000 ALTER TABLE `tab_user` DISABLE KEYS */;
INSERT INTO `tab_user` VALUES ('hgbao.idagroup@gmail.com','','$2b$12$CmKQH5k8uAvj2MrmF/HEsu6uE249pzt.4LgExplOeUpZWrJvKxHfW',1,1,1,'2026-06-29 13:18:59',0,'2026-06-30 04:51:13',0);
/*!40000 ALTER TABLE `tab_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_user_role`
--

DROP TABLE IF EXISTS `tab_user_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_user_role` (
  `user_id` bigint NOT NULL,
  `role_id` bigint NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_tab_user_role_role_id` (`role_id`),
  KEY `ix_tab_user_role_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_user_role`
--

LOCK TABLES `tab_user_role` WRITE;
/*!40000 ALTER TABLE `tab_user_role` DISABLE KEYS */;
INSERT INTO `tab_user_role` VALUES (1,1,1,'2026-06-29 13:18:59',0,'2026-06-29 13:18:59',0);
/*!40000 ALTER TABLE `tab_user_role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tab_warehouse`
--

DROP TABLE IF EXISTS `tab_warehouse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tab_warehouse` (
  `code` varchar(25) NOT NULL,
  `name` varchar(255) NOT NULL,
  `address` text NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tab_warehouse`
--

LOCK TABLES `tab_warehouse` WRITE;
/*!40000 ALTER TABLE `tab_warehouse` DISABLE KEYS */;
INSERT INTO `tab_warehouse` VALUES ('Agama','CÔNG TY CỔ PHẦN AGAMA','Lô 2, Đường số 2, Cụm Công nghiệp Đức Thuận, Ấp Tràm Lạc, Xã Mỹ Hạnh Bắc, Huyện Đức Hoà, Tỉnh Long An, Việt Nam',1,1,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Hà Long','CÔNG TY CỔ PHẦN HÓA CHẤT NÔNG NGHIỆP HÀ LONG','Lô A 204, Khu công nghiệp Thái Hòa , Xã Đức Lập Hạ, Huyện Đức Hoà, Tỉnh Long An, Việt Nam',1,2,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Âu Việt','CÔNG TY CỔ PHẦN PHÂN BÓN QUỐC TẾ ÂU VIỆT (CÔNG TY CP EVF)','Quốc lộ 1A, Ấp Long An B, Thị Trấn Cái Tắc, Huyện Châu Thành A, Tỉnh Hậu Giang, Việt Nam',1,3,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Basel','CÔNG TY TNHH BASEL THỤY SĨ','Lô H2A đường số 4, KCN Hải Sơn (GĐ 3+4), ấp Bình Tiền 2, Xã Đức Hòa Hạ, Huyện Đức Hoà, Tỉnh Long An',1,4,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Dego Cần Thơ','CÔNG TY TNHH DEGO HOLDING','Thửa đất số 86-Tờ bản đồ số 1, đường dẫn cầu Cần Thơ, QL 1A, KDC TTVH Tây Đô, P. Hưng Thạnh, Q. Cái Răng, TP. Cần Thơ (Cách trụ sở công an Quận Cái Răng 100m)',1,5,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Niềm Tin Việt','CÔNG TY TNHH PHÂN BÓN NIỀM TIN VIỆT','Ấp 2A, Xã Hưng Thạnh, H.Tháp Mười, Đồng Tháp',1,6,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Đại Tâm','CÔNG TY TNHH PRIMA - PHÁP - CHÂU ÂU','Lô B101 đường B. KCN Thái Hoà, Xã Đức Lập Hạ, Huyện Đức Hoà, Tỉnh Long An',1,7,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Pesticidex','CÔNG TY TNHH SÀN GIAO DỊCH THUỐC BẢO VỆ THỰC VẬT VIỆT NAM','Tầng 1, B19 đường dẫn cầu Cần Thơ, Quốc lộ 1A, KDC TTVH Tây Đô, Phường Hưng Thạnh, Quận Cái Răng, Thành phố Cần Thơ, Việt Nam',1,8,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Yamato','CÔNG TY TNHH SX TM YAMATO VN','Lô A20A Đường số 6, KCN Hải Sơn (GĐ 3+4), Xã Đức Hòa Hạ, Huyện Đức Hoà, Tỉnh Long An',1,9,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('ATC','CÔNG TY TNHH XUẤT NHẬP KHẨU HÓA CHẤT ATC','Số 87, Đường Lý Bôn, Phường Bình Đức, Tỉnh An Giang, Việt Nam',1,10,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Agrifuture','CÔNG TY TNHH AGRIFUTURE','Nhà Máy: Lô B123B, Đường số 7, KCN, ấp Tân Hòa, Đức Hòa, Long An\nVP: Phòng A4.04, Khu Phức Hợp Căn Hộ Nhật Hoa, 33 Nguyễn Hữu Thọ, Phường Tân Hưng, Thành phố Hồ Chí Minh, Việt Nam',1,11,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Thu Loan','Cty TNHH SX TM DV Thu Loan','699 tổ 34 Khóm Đông Thuận , Phường Đông Thành , Bình Minh, Vĩnh Long',1,12,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Thái Nông','CÔNG TY TNHH THƯƠNG MẠI THÁI NÔNG','73 Lạc Long Quân, Phường 1, Quận 11, Thành phố Hồ Chí Minh\n CN: Khu Công nghiệp Nhơn Trạch 3, Thị trấn Hiệp Phước, Huyện Nhơn Trạch, Tỉnh Đồng Nai, Việt Nam\n Giao Vật Tư: HKD Cơ Sở Phân Bón Lá Phú Hưng\n ĐC: 49A, đường số 27, Tân Lập, Tân Thông Hội, Củ Chi, HCM\n Người nhận: 0937 021 818 - Chị Bội',1,13,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('An Nông','CÔNG TY TNHH TẬP ĐOÀN AN NÔNG (AN GROUP)','Trụ sở : 464 Đường số 7, khu phố 8, Phường Tân Tạo, Quận Bình Tân, TP Hồ Chí Minh\n Nhà máy : Lô H7, Đường số 5, KCN Hải Sơn (GĐ 3+4), ấp Bình Tiền 2, Xã Đức Hòa Hạ, Huyện Đức Hoà, Tỉnh Long An, Việt Nam',1,14,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Kho Dr. Xanh','KHO DR XANH','Số 124 Võ Văn Kiệt, KV Bình Trung, P.Long Hòa, Q. Bình Thủy, Cần Thơ',1,15,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Kho B18','KHO B18','B18 đường dẫn cầu Cần Thơ, Quốc lộ 1A, KDC TTVH Tây Đô, Phường Cái Răng, Thành phố Cần Thơ',1,16,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Kho C1-2','Kho C1-2','Kho C1-2',1,17,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Kho F49 - Icare','KHO F49 - ICARE','nhà F49 (chạy qua trường lái Chiến Thắng) đường số 7, KDC Long Thịnh, Phường Phú Thứ, Cái Răng, Cần Thơ',1,18,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('Kho Lab Dego','KHO LAB DEGO','B19 đường dẫn cầu Cần Thơ, Quốc lộ 1A, KDC TTVH Tây Đô, Phường Cái Răng, Thành phố Cần Thơ',1,19,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0),('ADU','Công ty TNHH Nam Bắc','lô 215 đường số 5 KCN Thái Hòa, xã Đức Lập, Tây Ninh',1,20,'2026-06-30 03:01:08',0,'2026-06-30 03:01:08',0);
/*!40000 ALTER TABLE `tab_warehouse` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-01  2:14:31
