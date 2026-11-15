USE LibrosUyDB;
GO

-- Drop old tables if re-running cleanly
IF OBJECT_ID('sync_logs', 'U') IS NOT NULL DROP TABLE sync_logs;
IF OBJECT_ID('inventory_stock', 'U') IS NOT NULL DROP TABLE inventory_stock;
IF OBJECT_ID('books', 'U') IS NOT NULL DROP TABLE books;
IF OBJECT_ID('bookstores', 'U') IS NOT NULL DROP TABLE bookstores;
GO

-- 1. BOOKSTORES TABLE (All 29 Uruguayan stores & sync methods)
CREATE TABLE bookstores (
    bookstore_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(150) NOT NULL,
    website NVARCHAR(255) NULL,
    whatsapp VARCHAR(20) NULL, -- Formato internacional sin '+', ej. 59899123456
    instagram NVARCHAR(100) NULL, -- Usuario de Instagram, sin '@'
    specialty NVARCHAR(255) NOT NULL,
    address NVARCHAR(255) NOT NULL,
    department NVARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 6) NULL,
    longitude DECIMAL(10, 6) NULL,
    ingestion_method NVARCHAR(50) DEFAULT 'web_scraper', -- 'google_sheets' or 'web_scraper'
    sync_frequency NVARCHAR(50) DEFAULT 'twice_weekly',  -- 'daily' or 'twice_weekly'
    featured BIT DEFAULT 0,
    is_active BIT DEFAULT 1
);

-- 2. BOOKS TABLE (Master catalog normalized by ISBN-13)
CREATE TABLE books (
    book_id INT IDENTITY(1,1) PRIMARY KEY,
    isbn VARCHAR(20) NULL, -- Opcional: varias tiendas no cargan ISBN (único cuando existe, ver índice abajo)
    title NVARCHAR(255) NOT NULL,
    author NVARCHAR(255) NULL,
    genre NVARCHAR(100) NULL,
    cover_url NVARCHAR(500) NULL
);
CREATE UNIQUE INDEX UX_books_isbn ON books(isbn) WHERE isbn IS NOT NULL;
CREATE INDEX IX_books_title ON books(title);

-- 3. INVENTORY_STOCK TABLE (Links books to stores with price & availability)
CREATE TABLE inventory_stock (
    stock_id INT IDENTITY(1,1) PRIMARY KEY,
    bookstore_id INT NOT NULL,
    book_id INT NOT NULL,
    price_uyu DECIMAL(10, 2) NULL,
    stock_quantity INT DEFAULT 1,
    condition NVARCHAR(50) DEFAULT 'Nuevo', -- 'Nuevo', 'Usado', 'Raro'
    product_url NVARCHAR(500) NULL,
    external_id NVARCHAR(100) NULL, -- ID del producto en el sitio de la librería (scrapers)
    last_updated DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (bookstore_id) REFERENCES bookstores(bookstore_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX UX_inventory_store_external
    ON inventory_stock(bookstore_id, external_id) WHERE external_id IS NOT NULL;

-- 4. SYNC_LOGS TABLE (Audits daily sheet syncs & twice-weekly scraper runs)
CREATE TABLE sync_logs (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    bookstore_id INT NULL,
    sync_channel NVARCHAR(50) NOT NULL,
    status NVARCHAR(50) NOT NULL,
    records_processed INT DEFAULT 0,
    executed_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (bookstore_id) REFERENCES bookstores(bookstore_id) ON DELETE SET NULL
);
GO

-- SEED ALL 29 URUGUAYAN BOOKSTORES
INSERT INTO bookstores (name, website, specialty, address, department, latitude, longitude, ingestion_method, sync_frequency, featured) VALUES
(N'Librería Puro Verso', 'puroverso.uy', N'Ficción, No Ficción, Poesía, Juvenil', N'Av. 18 de Julio / Peatonal Sarandí 675', N'Montevideo', -34.9065, -56.2023, 'web_scraper', 'twice_weekly', 1),
(N'Escaramuza', 'escaramuza.com.uy', N'Catálogo General, Infantil, Café', N'Dr. Pablo de María 1185', N'Montevideo', -34.9080, -56.1712, 'web_scraper', 'twice_weekly', 1),
(N'Isadora Libros', 'isadoralibros.com.uy', N'Cómics, Medicina, Ficción', N'José Ellauri 661', N'Montevideo', -34.9165, -56.1568, 'web_scraper', 'twice_weekly', 0),
(N'Babilonia Libros', 'babilonia.uy', N'Usados, Raros, Agotados, Historia', N'Dr. Tristán Narvaja 1591', N'Montevideo', -34.9015, -56.1764, 'web_scraper', 'twice_weekly', 1),
(N'El Virrey', 'www.libreriaelvirrey.com.uy', N'Bestsellers, Novedades, Ficción', N'21 de Setiembre', N'Montevideo', -34.9142, -56.1589, 'web_scraper', 'twice_weekly', 0),
(N'Bookshop', 'bookshop.com.uy', N'Inglés, Catálogo General, Juvenil', N'José Enrique Rodó', N'Montevideo', -34.9048, -56.1742, 'web_scraper', 'twice_weekly', 1),
(N'Mosca', 'mosca.com.uy', N'Literatura, Educativos, Escolares', N'Av. 18 de Julio', N'Montevideo', -34.9058, -56.1852, 'web_scraper', 'twice_weekly', 1),
(N'Grupo Libros', 'grupolibros.com.uy', N'Catálogo General, Ficción', N'Tienda Online', N'Online', NULL, NULL, 'web_scraper', 'twice_weekly', 0),
(N'Diomedes', 'librosleidos.com.uy', N'Usados, Raros, Clásicos', N'Tienda Online', N'Online', NULL, NULL, 'web_scraper', 'twice_weekly', 0),
(N'Entrelibros', NULL, N'Catálogo General, Novedades', N'San José de Mayo', N'San José', -34.3375, -56.7136, 'google_sheets', 'daily', 0),
(N'Planetadelibros Uruguay', 'planetadelibros.com.uy', N'Editorial, Ficción, Juvenil, Romance', N'Tienda Online', N'Online', NULL, NULL, 'web_scraper', 'twice_weekly', 0),
(N'Librería El Altillo', NULL, N'Catálogo General, Local', N'Ciudad de la Costa', N'Canelones', -34.8222, -55.9547, 'google_sheets', 'daily', 0),
(N'Librería Ofipando', NULL, N'Catálogo General, Local, Escolares', N'Pando', N'Canelones', -34.7167, -55.9583, 'google_sheets', 'daily', 1),
(N'La Madriguera Libros', NULL, N'Catálogo General, Local', N'Canelones', N'Canelones', -34.5228, -56.2778, 'google_sheets', 'daily', 0),
(N'Espacio Chamangá', NULL, N'Independiente, Literatura, Arte', N'Maldonado', N'Maldonado', -34.9000, -54.9500, 'google_sheets', 'daily', 0),
(N'Bookshop (Sucursal Salto)', 'bookshop.com.uy', N'Catálogo General, Juvenil', N'Salto', N'Salto', -31.3833, -57.9667, 'web_scraper', 'twice_weekly', 0),
(N'Bookshop (Sucursal Rivera)', 'bookshop.com.uy', N'Catálogo General, Juvenil', N'Rivera', N'Rivera', -30.9053, -55.5508, 'web_scraper', 'twice_weekly', 0),
(N'Librería Entre Libros', NULL, N'Catálogo General', N'Paysandú', N'Paysandú', -32.3214, -58.0756, 'google_sheets', 'daily', 0),
(N'Origami Libros', NULL, N'Catálogo General, Ficción', N'Colonia del Sacramento', N'Colonia', -34.4626, -57.8398, 'google_sheets', 'daily', 0),
(N'Noctiluca', NULL, N'Librería Itinerante, Independiente', N'Móvil (VW Kombi - 19 departamentos)', N'Móvil', -34.6000, -56.0000, 'google_sheets', 'daily', 1),
(N'Lecturas Cómics', 'lecturascomics.com.uy', N'Cómics, Manga, Fantasía', N'Colonia 892', N'Montevideo', -34.9042, -56.1965, 'web_scraper', 'twice_weekly', 1),
(N'Librería Pocho', 'libreriapocho.com.uy', N'Manga, Educativos, General', N'Av. 18 de Julio 2198', N'Montevideo', -34.9012, -56.1668, 'web_scraper', 'twice_weekly', 0),
(N'Franca Comics', 'francacomics.uy', N'Cómics, Manga, Juvenil', N'Rafael Pérez del Puerto 736', N'Maldonado', -34.9088, -54.9581, 'web_scraper', 'twice_weekly', 0),
(N'Librería Lannister', 'librerialannister.com', N'Manga, Cómics, Fantasía', N'Tienda Online', N'Online', NULL, NULL, 'web_scraper', 'twice_weekly', 0),
(N'Librería Vila', 'libreriavila.com.uy', N'Manga, Cómics, Textos Estudio', N'Tristán Narvaja 1642', N'Montevideo', -34.9008, -56.1762, 'web_scraper', 'twice_weekly', 0),
(N'Librería Vanir', 'vanir.com.uy', N'Juvenil, Fantasía, Romance, Tarot', N'Belgrano 2934 BIS', N'Montevideo', -34.8875, -56.1552, 'web_scraper', 'twice_weekly', 1),
(N'Las Karamazov', 'laskaramazov.com.uy', N'Literatura Independiente, Ficción, Poesía', N'Av. Rivera 2670', N'Montevideo', -34.9035, -56.1538, 'web_scraper', 'twice_weekly', 1),
(N'Rizoma', 'rizomalajuanita.com', N'Catálogo Curado, Café, Arte', N'La Juanita, José Ignacio', N'Maldonado', -34.8415, -54.6522, 'web_scraper', 'twice_weekly', 0),
(N'Librería Montevideo', 'libreriamontevideo.com', N'Catálogo General, Historia, Nacionales', N'Montevideo', N'Montevideo', -34.9055, -56.1915, 'web_scraper', 'twice_weekly', 0);
GO

-- SEED STARTER BOOKS & INVENTORY STOCK FOR IMMEDIATE TESTING
INSERT INTO books (isbn, title, author, genre) VALUES
('9789974108929', N'La tregua', N'Mario Benedetti', N'Ficción'),
('9789875807471', N'Las venas abiertas de América Latina', N'Eduardo Galeano', N'Historia'),
('9788408275626', N'Alas de sangre (Fourth Wing)', N'Rebecca Yarros', N'Fantasía'),
('9788467942897', N'Chainsaw Man Vol. 1', N'Tatsuki Fujimoto', N'Manga');

INSERT INTO inventory_stock (bookstore_id, book_id, price_uyu, stock_quantity, condition, product_url) VALUES
(1, 1, 590.00, 5, N'Nuevo', 'https://puroverso.uy'),
(2, 1, 610.00, 3, N'Nuevo', 'https://escaramuza.com.uy'),
(13, 1, 580.00, 2, N'Nuevo', NULL),
(4, 2, 420.00, 1, N'Usado', 'https://babilonia.uy'),
(26, 3, 990.00, 4, N'Nuevo', 'https://vanir.com.uy'),
(6, 3, 1050.00, 6, N'Nuevo', 'https://bookshop.com.uy'),
(21, 4, 490.00, 8, N'Nuevo', 'https://lecturascomics.com.uy'),
(23, 4, 490.00, 3, N'Nuevo', 'https://francacomics.uy');
GO
-- WhatsApp e Instagram publicados por las librerías (ver migrations/003 y 004)
UPDATE bookstores SET whatsapp = '59899957216' WHERE website = 'babilonia.uy';
UPDATE bookstores SET whatsapp = '59897301685' WHERE website = 'bookshop.com.uy';
UPDATE bookstores SET whatsapp = '59891665568' WHERE website = 'escaramuza.com.uy';
UPDATE bookstores SET whatsapp = '59899295803' WHERE website = 'lecturascomics.com.uy';
UPDATE bookstores SET whatsapp = '59896057981' WHERE website = 'librerialannister.com';
UPDATE bookstores SET whatsapp = '59892221888' WHERE website = 'mosca.com.uy';
UPDATE bookstores SET whatsapp = '59893990904' WHERE website = 'www.libreriaelvirrey.com.uy';
UPDATE bookstores SET instagram = 'entre_libros_sanjose' WHERE name = N'Entrelibros';
GO
