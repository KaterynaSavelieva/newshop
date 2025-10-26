USE newshopdb;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,                  -- ключ
  email VARCHAR(120) NOT NULL UNIQUE,                 -- логін (email), має бути унікальним
  name VARCHAR(100) NOT NULL,                         -- ім'я (відображення)
  password_hash VARCHAR(255) NOT NULL,                -- хеш пароля
  role ENUM('admin','viewer') NOT NULL DEFAULT 'viewer', -- роль (можемо додати інші пізніше)
  is_active TINYINT(1) NOT NULL DEFAULT 1,            -- активний/заблокований
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- коли створений
  INDEX idx_users_email (email)                       -- індекс для швидкого пошуку
);

SHOW TABLES;
