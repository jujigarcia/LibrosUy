-- Agrega el número de WhatsApp de cada librería sin borrar los datos existentes.
-- Ejecutar una sola vez sobre una base creada con una versión anterior de schema.sql.
USE LibrosUyDB;
GO

IF COL_LENGTH('bookstores', 'whatsapp') IS NULL
    ALTER TABLE bookstores ADD whatsapp VARCHAR(20) NULL;
GO

-- Cargar los números a medida que cada librería los confirme, por ejemplo:
-- UPDATE bookstores SET whatsapp = '59899123456' WHERE name = N'Librería Puro Verso';
