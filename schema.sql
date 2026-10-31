CREATE DATABASE IF NOT EXISTS subscription_db;
USE subscription_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    service_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    cost DECIMAL(10, 2) NOT NULL,
    billing_cycle ENUM('Monthly', 'Yearly', 'Weekly') DEFAULT 'Monthly',
    next_renewal_date DATE NOT NULL,
    status ENUM('Active', 'Paused', 'Cancelled') DEFAULT 'Active',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);