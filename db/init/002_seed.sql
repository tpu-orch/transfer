-- Initial/seed data
-- Areas 1 and 2 are concentric Moscow zones; the inner zone has higher prices.
-- Other service-area centers use the airport coordinates from the flight service that Vadim provided may be reworked in future.

TRUNCATE TABLE bookings, area_tariffs, tariffs, areas RESTART IDENTITY CASCADE;

INSERT INTO areas (id, latitude, longitude, radius) VALUES
    (1, 55.7558, 37.6173, 40000), -- Moscow, outer zone
    (2, 55.7558, 37.6173, 15000), -- Moscow, inner zone
    (3, 59.8003, 30.2625, 35000), -- LED, Saint Petersburg
    (4, 43.4499, 39.9566, 35000), -- AER, Sochi
    (5, 55.6062, 49.2787, 35000), -- KZN, Kazan
    (6, 55.0126, 82.6507, 35000), -- OVB, Novosibirsk
    (7, 54.8900, 20.5926, 35000), -- KGD, Kaliningrad
    (8, 56.7431, 60.8027, 35000); -- SVX, Yekaterinburg

INSERT INTO tariffs (id, name) VALUES
    (1, 'Economy'),
    (2, 'Business');

INSERT INTO area_tariffs (id, area_id, tariff_id, price_per_km) VALUES
    (1, 1, 1, 65.00),  -- Moscow outer, Economy
    (2, 1, 2, 110.00), -- Moscow outer, Business
    (3, 2, 1, 85.00),  -- Moscow inner, Economy
    (4, 2, 2, 145.00), -- Moscow inner, Business
    (5, 3, 1, 60.00),  -- Saint Petersburg, Economy
    (6, 3, 2, 105.00), -- Saint Petersburg, Business
    (7, 4, 1, 70.00),  -- Sochi, Economy
    (8, 4, 2, 125.00), -- Sochi, Business
    (9, 5, 1, 55.00),  -- Kazan, Economy
    (10, 5, 2, 95.00), -- Kazan, Business
    (11, 6, 1, 50.00), -- Novosibirsk, Economy
    (12, 6, 2, 90.00), -- Novosibirsk, Business
    (13, 7, 1, 65.00), -- Kaliningrad, Economy
    (14, 7, 2, 115.00), -- Kaliningrad, Business
    (15, 8, 1, 55.00), -- Yekaterinburg, Economy
    (16, 8, 2, 100.00); -- Yekaterinburg, Business

ALTER TABLE areas ALTER COLUMN id RESTART WITH 9;
ALTER TABLE tariffs ALTER COLUMN id RESTART WITH 3;
ALTER TABLE area_tariffs ALTER COLUMN id RESTART WITH 17;
