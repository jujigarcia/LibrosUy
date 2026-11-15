-- Soporte para scrapers: libros sin ISBN e identificador del producto en cada tienda.
-- No borra datos. Ejecutar una sola vez sobre bases creadas antes de este cambio.
USE LibrosUyDB;
GO

-- 1. books.isbn pasa a ser opcional (muchas tiendas no cargan el ISBN),
--    manteniendo la unicidad para los que sí lo tienen.
DECLARE @uq SYSNAME = (
    SELECT kc.name FROM sys.key_constraints kc
    WHERE kc.parent_object_id = OBJECT_ID('books') AND kc.type = 'UQ'
);
IF @uq IS NOT NULL EXEC('ALTER TABLE books DROP CONSTRAINT ' + @uq);
GO
ALTER TABLE books ALTER COLUMN isbn VARCHAR(20) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_books_isbn')
    CREATE UNIQUE INDEX UX_books_isbn ON books(isbn) WHERE isbn IS NOT NULL;
GO

-- 2. Identificador del producto en el sitio de la librería, para actualizar en vez de duplicar.
IF COL_LENGTH('inventory_stock', 'external_id') IS NULL
    ALTER TABLE inventory_stock ADD external_id NVARCHAR(100) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_inventory_store_external')
    CREATE UNIQUE INDEX UX_inventory_store_external
        ON inventory_stock(bookstore_id, external_id) WHERE external_id IS NOT NULL;
GO

-- 3. Búsqueda de libros sin ISBN por título al sincronizar
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_books_title')
    CREATE INDEX IX_books_title ON books(title);
GO
