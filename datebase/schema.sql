-- 1. Create Tables
CREATE TABLE Stores (
    StoreID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Description NVARCHAR(500),
    WhatsAppNumber VARCHAR(20) NOT NULL,
    Address NVARCHAR(200) NOT NULL,
    City NVARCHAR(100) NOT NULL,
    Department NVARCHAR(50) NOT NULL,
    Latitude DECIMAL(10, 8),
    Longitude DECIMAL(11, 8),
    IsActive BIT DEFAULT 1
);

CREATE TABLE Tags (
    TagID INT IDENTITY(1,1) PRIMARY KEY,
    TagName NVARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Store_Tags (
    StoreID INT,
    TagID INT,
    PRIMARY KEY (StoreID, TagID),
    FOREIGN KEY (StoreID) REFERENCES Stores(StoreID) ON DELETE CASCADE,
    FOREIGN KEY (TagID) REFERENCES Tags(TagID) ON DELETE CASCADE
);

-- 2. Insert Base Tags
INSERT INTO Tags (TagName) VALUES 
('Fantasía'),
('Juvenil'),
('Romance'),
('Historia'),
('Autores Nacionales'),
('Cómics y Manga');

-- 3. Insert Starter Stores
INSERT INTO Stores (Name, Description, WhatsAppNumber, Address, City, Department, Latitude, Longitude, IsActive) VALUES 
('Librería Puro Verso', 'Gran variedad de literatura clásica, novedades y autores nacionales.', '59899111222', 'Peatonal Sarandí 675', 'Montevideo', 'Montevideo', -34.9065, -56.2023, 1),
('Escaramuza Libros', 'Especializada en literatura contemporánea, infantil y juvenil.', '59899333444', 'Dr. Pablo de María 1185', 'Montevideo', 'Montevideo', -34.9080, -56.1712, 1),
('Bookshop Canelones', 'Cadena de librerías con catálogo general y novelas juveniles.', '59899555666', 'Treinta y Tres 550', 'Canelones', 'Canelones', -34.5247, -56.2801, 1);

-- 4. Associate Stores with Tags (Store_Tags)
-- Puro Verso -> Autores Nacionales (5), Historia (4)
INSERT INTO Store_Tags (StoreID, TagID) VALUES (1, 5), (1, 4);

-- Escaramuza -> Fantasía (1), Juvenil (2), Romance (3)
INSERT INTO Store_Tags (StoreID, TagID) VALUES (2, 1), (2, 2), (2, 3);

-- Bookshop -> Juvenil (2), Romance (3)
INSERT INTO Store_Tags (StoreID, TagID) VALUES (3, 2), (3, 3);
