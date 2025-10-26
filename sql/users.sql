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

INSERT INTO users (email, name, password_hash, role, is_active)
VALUES (
  'admin@example.com',         -- логін
  'Admin',                     -- ім’я
  'pbkdf2:sha256:1000000$bFMbwgkPsAeq2ykB$4bdc29121cbb6bdf9ea4bd87254172d4b79da9e5abb560703e113dd02689da6c',  -- сюди повністю встав свій хеш
  'admin',                     -- роль
  1                            -- активний
);

SELECT id, email, name, role, created_at FROM users;
