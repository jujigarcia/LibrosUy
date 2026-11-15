-- Instagram de las librerías y correcciones de datos (15/11/2026).
USE LibrosUyDB;
GO

IF COL_LENGTH('bookstores', 'instagram') IS NULL
    ALTER TABLE bookstores ADD instagram NVARCHAR(100) NULL; -- usuario, sin '@'
GO

-- El Virrey: el sitio solo responde con "www." y usa Fenicio (se sincroniza con el scraper)
UPDATE bookstores
SET website = 'www.libreriaelvirrey.com.uy', whatsapp = COALESCE(whatsapp, '59893990904')
WHERE website = 'libreriaelvirrey.com.uy';

-- Entrelibros: librería de San José sin sitio web (entrelibros.com.uy es otro proyecto, un blog)
UPDATE bookstores
SET website = NULL, instagram = 'entre_libros_sanjose',
    address = N'San José de Mayo', department = N'San José',
    latitude = -34.3375, longitude = -56.7136,
    ingestion_method = 'google_sheets', sync_frequency = 'daily'
WHERE name = N'Entrelibros';
GO
