-- ============================================
-- YOLO 系统数据库建表语句
-- 数据库名称：yolo_system
-- 字符集：utf8mb4
-- 创建时间：2026-03-29
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS yolo_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE yolo_system;

-- ============================================
-- 1. 宠物分类表 (pet_categories)
-- 用于存储宠物的分类信息，支持多级分类
-- ============================================
CREATE TABLE IF NOT EXISTS `pet_categories` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '分类 ID',
    `name` VARCHAR(50) NOT NULL COMMENT '分类名称（中文）',
    `name_en` VARCHAR(50) COMMENT '分类名称（英文）',
    `parent_id` INT COMMENT '父分类 ID，支持多级分类',
    `icon` VARCHAR(100) COMMENT '分类图标 URL',
    `sort_order` INT DEFAULT 0 COMMENT '排序顺序',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`parent_id`) REFERENCES `pet_categories`(`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX `idx_name` (`name`),
    INDEX `idx_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='宠物分类表';

-- ============================================
-- 2. 宠物品种表 (pet_breeds)
-- 用于存储宠物品种的详细信息
-- ============================================
CREATE TABLE IF NOT EXISTS `pet_breeds` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '品种 ID',
    `name` VARCHAR(50) NOT NULL COMMENT '品种名称（中文）',
    `name_en` VARCHAR(50) NOT NULL COMMENT '品种名称（英文）',
    `category_id` INT NOT NULL COMMENT '所属分类 ID',
    `image` LONGBLOB COMMENT '品种图片（二进制数据）',
    `description` TEXT COMMENT '品种描述',
    `origin` VARCHAR(100) COMMENT '起源地',
    `personality` TEXT COMMENT '性格特点',
    `care_tips` TEXT COMMENT '饲养要点',
    `diet_needs` TEXT COMMENT '饮食需求',
    `health_issues` TEXT COMMENT '健康问题',
    `exercise_needs` VARCHAR(50) COMMENT '运动需求',
    `size` VARCHAR(20) COMMENT '体型大小',
    `lifespan` VARCHAR(50) COMMENT '寿命',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`category_id`) REFERENCES `pet_categories`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_name` (`name`),
    INDEX `idx_category_id` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='宠物品种表';

-- ============================================
-- 3. 用户表 (users)
-- 用于存储系统用户信息，支持管理员和普通用户
-- ============================================
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户 ID',
    `username` VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    `password_hash` VARCHAR(255) COMMENT '密码哈希值',
    `email` VARCHAR(100) UNIQUE COMMENT '邮箱地址',
    `avatar` LONGBLOB COMMENT '用户头像（二进制数据）',
    `nickname` VARCHAR(50) COMMENT '昵称',
    `role` VARCHAR(20) DEFAULT 'user' NOT NULL COMMENT '用户角色：admin=管理员，user=普通用户',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `last_login` DATETIME COMMENT '最后登录时间',
    `is_verified` BOOLEAN DEFAULT FALSE COMMENT '邮箱是否已验证',
    `verification_code` VARCHAR(6) COMMENT '邮箱验证码',
    `verification_expire` DATETIME COMMENT '验证码过期时间',
    INDEX `idx_username` (`username`),
    INDEX `idx_email` (`email`),
    INDEX `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================

-- ============================================
-- 数据说明：
-- 1. pet_categories: 支持多级分类，通过 parent_id 实现树形结构
-- 2. pet_breeds: 存储宠物品种详细信息，包含饲养指南
-- 3. users: 用户表，支持邮箱验证和角色管理
--
-- 外键约束：
-- - pet_breeds.category_id -> pet_categories.id (级联删除和更新)
-- - articles.author_id -> users.id (级联删除和更新)
-- - pet_categories.parent_id -> pet_categories.id (自引用，设置为 NULL)
--
-- 索引优化：
-- - 所有主键自动创建索引
-- - 常用查询字段创建索引（username, email, name 等）
-- - 外键字段创建索引优化关联查询
-- ============================================