-- Números de WhatsApp publicados por cada librería en su propio sitio web (relevados el 15/11/2026).
-- Solo completa los que todavía no tienen número cargado.
USE LibrosUyDB;
GO
UPDATE bookstores SET whatsapp = '59899957216' WHERE website = 'babilonia.uy'          AND whatsapp IS NULL;
UPDATE bookstores SET whatsapp = '59897301685' WHERE website = 'bookshop.com.uy'       AND whatsapp IS NULL;
UPDATE bookstores SET whatsapp = '59891665568' WHERE website = 'escaramuza.com.uy'     AND whatsapp IS NULL;
UPDATE bookstores SET whatsapp = '59899295803' WHERE website = 'lecturascomics.com.uy' AND whatsapp IS NULL;
UPDATE bookstores SET whatsapp = '59896057981' WHERE website = 'librerialannister.com' AND whatsapp IS NULL;
UPDATE bookstores SET whatsapp = '59892221888' WHERE website = 'mosca.com.uy'          AND whatsapp IS NULL;
GO
