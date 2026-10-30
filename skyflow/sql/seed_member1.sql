-- =====================================================================
-- SkyFlow Database System
-- Seed Data: seed_member1.sql
-- Contains:
-- 1. 12 Indian Airports (frozen 3-letter IATA codes)
-- 2. 1-3 Runways per airport with realistic designators & dimensions (m)
-- 3. Gates per airport across terminals (~8-15 per airport)
-- 4. Shared minimal stubs (Airlines, Aircraft, Flights) for FK resolution
-- 5. ~40 Gate Assignments
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. AIRPORTS (12 Major Indian Airports)
-- ---------------------------------------------------------------------
INSERT INTO airport (airport_code, name, city, elevation_ft, latitude, longitude) VALUES
('DEL', 'Indira Gandhi International Airport', 'New Delhi', 777, 28.556160, 77.100281),
('BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'Mumbai', 39, 19.089560, 72.865616),
('BLR', 'Kempegowda International Airport', 'Bengaluru', 3000, 13.198639, 77.706596),
('MAA', 'Chennai International Airport', 'Chennai', 52, 12.994112, 80.170868),
('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad', 2024, 17.240500, 78.429400),
('CCU', 'Netaji Subhash Chandra Bose International Airport', 'Kolkata', 16, 22.654722, 88.446667),
('AMD', 'Sardar Vallabhbhai Patel International Airport', 'Ahmedabad', 189, 23.077222, 72.634722),
('COK', 'Cochin International Airport', 'Kochi', 30, 10.152000, 76.401900),
('PNQ', 'Pune Airport', 'Pune', 1942, 18.582222, 73.919722),
('GOX', 'Manohar International Airport (Mopa)', 'Goa', 558, 15.766111, 73.868889),
('JAI', 'Jaipur International Airport', 'Jaipur', 1263, 26.824167, 75.812222),
('GAU', 'Lokpriya Gopinath Bordoloi International Airport', 'Guwahati', 162, 26.106111, 91.585833)
ON CONFLICT (airport_code) DO NOTHING;

-- ---------------------------------------------------------------------
-- 2. RUNWAYS (1 to 3 per airport)
-- ---------------------------------------------------------------------
INSERT INTO runway (airport_code, runway_designator, length_m, width_m, surface_type, current_status) VALUES
-- DEL (3 major runways)
('DEL', '10/28', 3810, 45, 'ASPHALT', 'AVAILABLE'),
('DEL', '11R/29L', 4430, 60, 'CONCRETE', 'AVAILABLE'),
('DEL', '09/27', 2816, 45, 'ASPHALT', 'OCCUPIED'),

-- BOM (2 intersecting runways)
('BOM', '09/27', 3660, 60, 'ASPHALT', 'AVAILABLE'),
('BOM', '14/32', 2990, 45, 'ASPHALT', 'AVAILABLE'),

-- BLR (2 parallel runways)
('BLR', '09L/27R', 4000, 45, 'ASPHALT', 'AVAILABLE'),
('BLR', '09R/27L', 4000, 45, 'CONCRETE', 'AVAILABLE'),

-- MAA (2 intersecting runways)
('MAA', '07/25', 3658, 45, 'ASPHALT', 'AVAILABLE'),
('MAA', '12/30', 2045, 45, 'ASPHALT', 'CLOSED'),

-- HYD (2 runways)
('HYD', '09L/27R', 4260, 60, 'ASPHALT', 'AVAILABLE'),
('HYD', '09R/27L', 3700, 45, 'ASPHALT', 'AVAILABLE'),

-- CCU (2 parallel runways)
('CCU', '01R/19L', 3627, 45, 'ASPHALT', 'AVAILABLE'),
('CCU', '01L/19R', 2790, 45, 'ASPHALT', 'AVAILABLE'),

-- AMD
('AMD', '05/23', 3505, 45, 'ASPHALT', 'AVAILABLE'),

-- COK
('COK', '09/27', 3400, 45, 'ASPHALT', 'AVAILABLE'),

-- PNQ
('PNQ', '10/28', 2539, 45, 'CONCRETE', 'OCCUPIED'),

-- GOX
('GOX', '09/27', 3500, 45, 'ASPHALT', 'AVAILABLE'),

-- JAI
('JAI', '09/27', 3407, 45, 'ASPHALT', 'AVAILABLE'),

-- GAU
('GAU', '02/20', 3110, 45, 'ASPHALT', 'AVAILABLE');

-- ---------------------------------------------------------------------
-- 3. GATES (8 to 15 per airport across terminals)
-- ---------------------------------------------------------------------
-- DEL Gates (T1, T2, T3)
INSERT INTO gate (airport_code, terminal, gate_number, gate_type, current_status) VALUES
('DEL', 'T3', '301', 'CONTACT', 'OCCUPIED'),
('DEL', 'T3', '302', 'CONTACT', 'AVAILABLE'),
('DEL', 'T3', '303', 'CONTACT', 'AVAILABLE'),
('DEL', 'T3', '304', 'CONTACT', 'MAINTENANCE'),
('DEL', 'T3', '305', 'REMOTE',  'AVAILABLE'),
('DEL', 'T2', '201', 'CONTACT', 'AVAILABLE'),
('DEL', 'T2', '202', 'CONTACT', 'OCCUPIED'),
('DEL', 'T2', '203', 'REMOTE',  'AVAILABLE'),
('DEL', 'T1', '101', 'CONTACT', 'AVAILABLE'),
('DEL', 'T1', '102', 'CONTACT', 'AVAILABLE'),
('DEL', 'T1', '103', 'REMOTE',  'AVAILABLE'),
('DEL', 'T1', '104', 'REMOTE',  'AVAILABLE');

-- BOM Gates (T1, T2)
INSERT INTO gate (airport_code, terminal, gate_number, gate_type, current_status) VALUES
('BOM', 'T2', '41', 'CONTACT', 'OCCUPIED'),
('BOM', 'T2', '42', 'CONTACT', 'AVAILABLE'),
('BOM', 'T2', '43', 'CONTACT', 'AVAILABLE'),
('BOM', 'T2', '44', 'CONTACT', 'AVAILABLE'),
('BOM', 'T2', '45', 'REMOTE',  'AVAILABLE'),
('BOM', 'T1', '01', 'CONTACT', 'AVAILABLE'),
('BOM', 'T1', '02', 'CONTACT', 'OCCUPIED'),
('BOM', 'T1', '03', 'REMOTE',  'AVAILABLE'),
('BOM', 'T1', '04', 'REMOTE',  'MAINTENANCE');

-- BLR Gates (T1, T2)
INSERT INTO gate (airport_code, terminal, gate_number, gate_type, current_status) VALUES
('BLR', 'T1', 'G01', 'CONTACT', 'AVAILABLE'),
('BLR', 'T1', 'G02', 'CONTACT', 'OCCUPIED'),
('BLR', 'T1', 'G03', 'CONTACT', 'AVAILABLE'),
('BLR', 'T1', 'G04', 'REMOTE',  'AVAILABLE'),
('BLR', 'T2', 'G21', 'CONTACT', 'AVAILABLE'),
('BLR', 'T2', 'G22', 'CONTACT', 'OCCUPIED'),
('BLR', 'T2', 'G23', 'CONTACT', 'AVAILABLE'),
('BLR', 'T2', 'G24', 'REMOTE',  'AVAILABLE');

-- MAA Gates (T1, T4)
INSERT INTO gate (airport_code, terminal, gate_number, gate_type, current_status) VALUES
('MAA', 'T1', '1', 'CONTACT', 'AVAILABLE'),
('MAA', 'T1', '2', 'CONTACT', 'AVAILABLE'),
('MAA', 'T1', '3', 'REMOTE',  'AVAILABLE'),
('MAA', 'T1', '4', 'REMOTE',  'AVAILABLE'),
('MAA', 'T4', '11', 'CONTACT', 'OCCUPIED'),
('MAA', 'T4', '12', 'CONTACT', 'AVAILABLE'),
('MAA', 'T4', '13', 'REMOTE',  'AVAILABLE'),
('MAA', 'T4', '14', 'REMOTE',  'AVAILABLE');

-- HYD Gates (Main Terminal)
INSERT INTO gate (airport_code, terminal, gate_number, gate_type, current_status) VALUES
('HYD', 'T1', 'H01', 'CONTACT', 'AVAILABLE'),
('HYD', 'T1', 'H02', 'CONTACT', 'OCCUPIED'),
('HYD', 'T1', 'H03', 'CONTACT', 'AVAILABLE'),
('HYD', 'T1', 'H04', 'CONTACT', 'AVAILABLE'),
('HYD', 'T1', 'H05', 'REMOTE',  'AVAILABLE'),
('HYD', 'T1', 'H06', 'REMOTE',  'AVAILABLE'),
('HYD', 'T1', 'H07', 'REMOTE',  'AVAILABLE'),
('HYD', 'T1', 'H08', 'REMOTE',  'AVAILABLE');

-- CCU Gates (T2)
INSERT INTO gate (airport_code, terminal, gate_number, gate_type, current_status) VALUES
('CCU', 'T2', 'C1', 'CONTACT', 'AVAILABLE'),
('CCU', 'T2', 'C2', 'CONTACT', 'OCCUPIED'),
('CCU', 'T2', 'C3', 'CONTACT', 'AVAILABLE'),
('CCU', 'T2', 'C4', 'CONTACT', 'AVAILABLE'),
('CCU', 'T2', 'C5', 'REMOTE',  'AVAILABLE'),
('CCU', 'T2', 'C6', 'REMOTE',  'AVAILABLE'),
('CCU', 'T2', 'C7', 'REMOTE',  'AVAILABLE'),
('CCU', 'T2', 'C8', 'REMOTE',  'MAINTENANCE');

-- AMD, COK, PNQ, GOX, JAI, GAU Gates (8 each)
INSERT INTO gate (airport_code, terminal, gate_number, gate_type, current_status) VALUES
('AMD', 'T1', 'A1', 'CONTACT', 'AVAILABLE'), ('AMD', 'T1', 'A2', 'CONTACT', 'AVAILABLE'),
('AMD', 'T1', 'A3', 'REMOTE', 'AVAILABLE'),  ('AMD', 'T1', 'A4', 'REMOTE', 'AVAILABLE'),
('AMD', 'T2', 'A5', 'CONTACT', 'AVAILABLE'), ('AMD', 'T2', 'A6', 'CONTACT', 'AVAILABLE'),
('AMD', 'T2', 'A7', 'REMOTE', 'AVAILABLE'),  ('AMD', 'T2', 'A8', 'REMOTE', 'AVAILABLE'),

('COK', 'T1', 'K1', 'CONTACT', 'AVAILABLE'), ('COK', 'T1', 'K2', 'CONTACT', 'AVAILABLE'),
('COK', 'T1', 'K3', 'REMOTE', 'AVAILABLE'),  ('COK', 'T1', 'K4', 'REMOTE', 'AVAILABLE'),
('COK', 'T3', 'K5', 'CONTACT', 'AVAILABLE'), ('COK', 'T3', 'K6', 'CONTACT', 'AVAILABLE'),
('COK', 'T3', 'K7', 'REMOTE', 'AVAILABLE'),  ('COK', 'T3', 'K8', 'REMOTE', 'AVAILABLE'),

('PNQ', 'T1', 'P1', 'CONTACT', 'AVAILABLE'), ('PNQ', 'T1', 'P2', 'CONTACT', 'AVAILABLE'),
('PNQ', 'T1', 'P3', 'REMOTE', 'AVAILABLE'),  ('PNQ', 'T1', 'P4', 'REMOTE', 'AVAILABLE'),
('PNQ', 'T1', 'P5', 'REMOTE', 'AVAILABLE'),  ('PNQ', 'T1', 'P6', 'REMOTE', 'AVAILABLE'),
('PNQ', 'T1', 'P7', 'REMOTE', 'AVAILABLE'),  ('PNQ', 'T1', 'P8', 'REMOTE', 'AVAILABLE'),

('GOX', 'T1', 'G1', 'CONTACT', 'AVAILABLE'), ('GOX', 'T1', 'G2', 'CONTACT', 'AVAILABLE'),
('GOX', 'T1', 'G3', 'CONTACT', 'AVAILABLE'), ('GOX', 'T1', 'G4', 'CONTACT', 'AVAILABLE'),
('GOX', 'T1', 'G5', 'REMOTE', 'AVAILABLE'),  ('GOX', 'T1', 'G6', 'REMOTE', 'AVAILABLE'),
('GOX', 'T1', 'G7', 'REMOTE', 'AVAILABLE'),  ('GOX', 'T1', 'G8', 'REMOTE', 'AVAILABLE'),

('JAI', 'T2', 'J1', 'CONTACT', 'AVAILABLE'), ('JAI', 'T2', 'J2', 'CONTACT', 'AVAILABLE'),
('JAI', 'T2', 'J3', 'REMOTE', 'AVAILABLE'),  ('JAI', 'T2', 'J4', 'REMOTE', 'AVAILABLE'),
('JAI', 'T2', 'J5', 'CONTACT', 'AVAILABLE'), ('JAI', 'T2', 'J6', 'CONTACT', 'AVAILABLE'),
('JAI', 'T2', 'J7', 'REMOTE', 'AVAILABLE'),  ('JAI', 'T2', 'J8', 'REMOTE', 'AVAILABLE'),

('GAU', 'T1', 'U1', 'CONTACT', 'AVAILABLE'), ('GAU', 'T1', 'U2', 'CONTACT', 'AVAILABLE'),
('GAU', 'T1', 'U3', 'REMOTE', 'AVAILABLE'),  ('GAU', 'T1', 'U4', 'REMOTE', 'AVAILABLE'),
('GAU', 'T1', 'U5', 'REMOTE', 'AVAILABLE'),  ('GAU', 'T1', 'U6', 'REMOTE', 'AVAILABLE'),
('GAU', 'T1', 'U7', 'REMOTE', 'AVAILABLE'),  ('GAU', 'T1', 'U8', 'REMOTE', 'AVAILABLE');

-- ---------------------------------------------------------------------
-- 4. SHARED STUB DATA (Airlines, Aircraft, Flights)
-- Allows gate_assignment and queries to execute cleanly independently
-- ---------------------------------------------------------------------
INSERT INTO airline (airline_code, airline_name, country) VALUES
('6E', 'IndiGo', 'India'),
('AI', 'Air India', 'India'),
('UK', 'Vistara', 'India'),
('SG', 'SpiceJet', 'India'),
('QP', 'Akasa Air', 'India')
ON CONFLICT (airline_code) DO NOTHING;

INSERT INTO aircraft (registration_no, airline_code, model, capacity) VALUES
('VT-IFJ', '6E', 'Airbus A320neo', 186),
('VT-CIO', '6E', 'Airbus A321neo', 222),
('VT-EXH', 'AI', 'Boeing 787-8', 256),
('VT-TTB', 'UK', 'Airbus A320neo', 164),
('VT-SLD', 'SG', 'Boeing 737-800', 189)
ON CONFLICT (registration_no) DO NOTHING;

-- Stub Flights for Date: 2026-10-30
INSERT INTO flight (flight_number, flight_date, airline_code, aircraft_id, origin_airport, destination_airport, scheduled_departure, scheduled_arrival, current_status, assigned_runway_id) VALUES
('6E101', '2026-10-30', '6E', 1, 'DEL', 'BOM', '2026-10-30 06:00:00', '2026-10-30 08:15:00', 'LANDED', 1),
('6E102', '2026-10-30', '6E', 1, 'BOM', 'DEL', '2026-10-30 09:00:00', '2026-10-30 11:15:00', 'LANDED', 2),
('6E103', '2026-10-30', '6E', 2, 'DEL', 'BLR', '2026-10-30 07:30:00', '2026-10-30 10:15:00', 'LANDED', 1),
('6E104', '2026-10-30', '6E', 2, 'BLR', 'DEL', '2026-10-30 11:00:00', '2026-10-30 13:45:00', 'AIRBORNE', 2),
('AI201', '2026-10-30', 'AI', 3, 'BOM', 'DEL', '2026-10-30 07:00:00', '2026-10-30 09:10:00', 'LANDED', 2),
('AI202', '2026-10-30', 'AI', 3, 'DEL', 'BOM', '2026-10-30 10:30:00', '2026-10-30 12:45:00', 'TAXIING', 1),
('UK801', '2026-10-30', 'UK', 4, 'DEL', 'CCU', '2026-10-30 08:00:00', '2026-10-30 10:15:00', 'LANDED', 1),
('UK802', '2026-10-30', 'UK', 4, 'CCU', 'DEL', '2026-10-30 11:00:00', '2026-10-30 13:20:00', 'SCHEDULED', 2),
('SG301', '2026-10-30', 'SG', 5, 'DEL', 'HYD', '2026-10-30 06:45:00', '2026-10-30 09:00:00', 'LANDED', 1),
('SG302', '2026-10-30', 'SG', 5, 'HYD', 'DEL', '2026-10-30 09:45:00', '2026-10-30 12:00:00', 'AIRBORNE', 2),
('6E201', '2026-10-30', '6E', 1, 'BLR', 'BOM', '2026-10-30 14:00:00', '2026-10-30 15:40:00', 'SCHEDULED', 6),
('6E202', '2026-10-30', '6E', 2, 'BOM', 'BLR', '2026-10-30 16:30:00', '2026-10-30 18:10:00', 'SCHEDULED', 4),
('AI305', '2026-10-30', 'AI', 3, 'MAA', 'DEL', '2026-10-30 06:15:00', '2026-10-30 09:05:00', 'LANDED', 8),
('AI306', '2026-10-30', 'AI', 3, 'DEL', 'MAA', '2026-10-30 10:00:00', '2026-10-30 12:50:00', 'BOARDING', 1),
('UK911', '2026-10-30', 'UK', 4, 'BOM', 'MAA', '2026-10-30 08:30:00', '2026-10-30 10:25:00', 'LANDED', 5),
('UK912', '2026-10-30', 'UK', 4, 'MAA', 'BOM', '2026-10-30 11:15:00', '2026-10-30 13:10:00', 'SCHEDULED', 8),
('SG401', '2026-10-30', 'SG', 5, 'HYD', 'BLR', '2026-10-30 07:15:00', '2026-10-30 08:30:00', 'LANDED', 10),
('SG402', '2026-10-30', 'SG', 5, 'BLR', 'HYD', '2026-10-30 09:15:00', '2026-10-30 10:30:00', 'LANDED', 6),
('6E501', '2026-10-30', '6E', 1, 'CCU', 'GAU', '2026-10-30 06:30:00', '2026-10-30 07:45:00', 'LANDED', 12),
('6E502', '2026-10-30', '6E', 1, 'GAU', 'CCU', '2026-10-30 08:30:00', '2026-10-30 09:45:00', 'LANDED', 12),
('AI401', '2026-10-30', 'AI', 3, 'AMD', 'DEL', '2026-10-30 07:00:00', '2026-10-30 08:35:00', 'LANDED', 14),
('AI402', '2026-10-30', 'AI', 3, 'DEL', 'AMD', '2026-10-30 09:30:00', '2026-10-30 11:05:00', 'AIRBORNE', 2),
('6E601', '2026-10-30', '6E', 2, 'COK', 'BLR', '2026-10-30 06:10:00', '2026-10-30 07:20:00', 'LANDED', 15),
('6E602', '2026-10-30', '6E', 2, 'BLR', 'COK', '2026-10-30 08:10:00', '2026-10-30 09:20:00', 'LANDED', 6),
('UK701', '2026-10-30', 'UK', 4, 'PNQ', 'DEL', '2026-10-30 06:50:00', '2026-10-30 09:00:00', 'LANDED', 16),
('UK702', '2026-10-30', 'UK', 4, 'DEL', 'PNQ', '2026-10-30 10:00:00', '2026-10-30 12:10:00', 'SCHEDULED', 1),
('SG501', '2026-10-30', 'SG', 5, 'GOX', 'BOM', '2026-10-30 07:45:00', '2026-10-30 09:00:00', 'LANDED', 17),
('SG502', '2026-10-30', 'SG', 5, 'BOM', 'GOX', '2026-10-30 10:00:00', '2026-10-30 11:15:00', 'SCHEDULED', 4),
('6E701', '2026-10-30', '6E', 1, 'JAI', 'BOM', '2026-10-30 06:20:00', '2026-10-30 08:05:00', 'LANDED', 18),
('6E702', '2026-10-30', '6E', 1, 'BOM', 'JAI', '2026-10-30 09:00:00', '2026-10-30 10:45:00', 'AIRBORNE', 5),
('AI501', '2026-10-30', 'AI', 3, 'DEL', 'JAI', '2026-10-30 12:00:00', '2026-10-30 13:00:00', 'SCHEDULED', 1),
('AI502', '2026-10-30', 'AI', 3, 'JAI', 'DEL', '2026-10-30 14:00:00', '2026-10-30 15:00:00', 'SCHEDULED', 18),
('UK601', '2026-10-30', 'UK', 4, 'MAA', 'CCU', '2026-10-30 06:30:00', '2026-10-30 08:45:00', 'LANDED', 8),
('UK602', '2026-10-30', 'UK', 4, 'CCU', 'MAA', '2026-10-30 09:30:00', '2026-10-30 11:45:00', 'AIRBORNE', 12),
('6E801', '2026-10-30', '6E', 2, 'HYD', 'AMD', '2026-10-30 06:00:00', '2026-10-30 07:50:00', 'LANDED', 10),
('6E802', '2026-10-30', '6E', 2, 'AMD', 'HYD', '2026-10-30 08:30:00', '2026-10-30 10:15:00', 'LANDED', 14),
('SG601', '2026-10-30', 'SG', 5, 'COK', 'MAA', '2026-10-30 07:00:00', '2026-10-30 08:15:00', 'LANDED', 15),
('SG602', '2026-10-30', 'SG', 5, 'MAA', 'COK', '2026-10-30 09:00:00', '2026-10-30 10:15:00', 'LANDED', 8),
('6E901', '2026-10-30', '6E', 1, 'GAU', 'DEL', '2026-10-30 10:30:00', '2026-10-30 13:15:00', 'SCHEDULED', 19),
('6E902', '2026-10-30', '6E', 1, 'DEL', 'GAU', '2026-10-30 14:00:00', '2026-10-30 16:45:00', 'SCHEDULED', 1)
ON CONFLICT (flight_number, flight_date) DO NOTHING;

-- ---------------------------------------------------------------------
-- 5. GATE ASSIGNMENTS (40 realistic non-overlapping assignments)
-- ---------------------------------------------------------------------
INSERT INTO gate_assignment (gate_id, flight_id, assigned_from, assigned_until, status) VALUES
(1, 1, '2026-10-30 05:00:00', '2026-10-30 06:05:00', 'COMPLETED'),
(13, 1, '2026-10-30 08:15:00', '2026-10-30 09:00:00', 'COMPLETED'),
(2, 3, '2026-10-30 06:30:00', '2026-10-30 07:35:00', 'COMPLETED'),
(21, 3, '2026-10-30 10:15:00', '2026-10-30 11:15:00', 'COMPLETED'),
(14, 5, '2026-10-30 06:00:00', '2026-10-30 07:05:00', 'COMPLETED'),
(3, 5, '2026-10-30 09:10:00', '2026-10-30 10:30:00', 'COMPLETED'),
(6, 7, '2026-10-30 07:00:00', '2026-10-30 08:05:00', 'COMPLETED'),
(37, 7, '2026-10-30 10:15:00', '2026-10-30 11:00:00', 'COMPLETED'),
(7, 9, '2026-10-30 05:45:00', '2026-10-30 06:50:00', 'COMPLETED'),
(30, 9, '2026-10-30 09:00:00', '2026-10-30 09:50:00', 'COMPLETED'),

(22, 11, '2026-10-30 13:00:00', '2026-10-30 14:05:00', 'CONFIRMED'),
(15, 12, '2026-10-30 15:30:00', '2026-10-30 16:35:00', 'CONFIRMED'),
(26, 13, '2026-10-30 05:15:00', '2026-10-30 06:20:00', 'COMPLETED'),
(1, 14, '2026-10-30 09:00:00', '2026-10-30 10:05:00', 'OCCUPIED'),
(16, 15, '2026-10-30 07:30:00', '2026-10-30 08:35:00', 'COMPLETED'),
(27, 16, '2026-10-30 10:15:00', '2026-10-30 11:20:00', 'CONFIRMED'),
(31, 17, '2026-10-30 06:15:00', '2026-10-30 07:20:00', 'COMPLETED'),
(23, 18, '2026-10-30 08:15:00', '2026-10-30 09:20:00', 'COMPLETED'),
(38, 19, '2026-10-30 05:30:00', '2026-10-30 06:35:00', 'COMPLETED'),
(69, 20, '2026-10-30 07:30:00', '2026-10-30 08:35:00', 'COMPLETED'),

(45, 21, '2026-10-30 06:00:00', '2026-10-30 07:05:00', 'COMPLETED'),
(2, 22, '2026-10-30 08:30:00', '2026-10-30 09:35:00', 'COMPLETED'),
(49, 23, '2026-10-30 05:10:00', '2026-10-30 06:15:00', 'COMPLETED'),
(24, 24, '2026-10-30 07:10:00', '2026-10-30 08:15:00', 'COMPLETED'),
(53, 25, '2026-10-30 05:50:00', '2026-10-30 06:55:00', 'COMPLETED'),
(4, 26, '2026-10-30 09:00:00', '2026-10-30 10:05:00', 'CONFIRMED'),
(57, 27, '2026-10-30 06:45:00', '2026-10-30 07:50:00', 'COMPLETED'),
(17, 28, '2026-10-30 09:00:00', '2026-10-30 10:05:00', 'CONFIRMED'),
(61, 29, '2026-10-30 05:20:00', '2026-10-30 06:25:00', 'COMPLETED'),
(18, 30, '2026-10-30 08:00:00', '2026-10-30 09:05:00', 'COMPLETED'),

(5, 31, '2026-10-30 11:00:00', '2026-10-30 12:05:00', 'CONFIRMED'),
(62, 32, '2026-10-30 13:00:00', '2026-10-30 14:05:00', 'CONFIRMED'),
(28, 33, '2026-10-30 05:30:00', '2026-10-30 06:35:00', 'COMPLETED'),
(39, 34, '2026-10-30 08:30:00', '2026-10-30 09:35:00', 'COMPLETED'),
(32, 35, '2026-10-30 05:00:00', '2026-10-30 06:05:00', 'COMPLETED'),
(46, 36, '2026-10-30 07:30:00', '2026-10-30 08:35:00', 'COMPLETED'),
(50, 37, '2026-10-30 06:00:00', '2026-10-30 07:05:00', 'COMPLETED'),
(29, 38, '2026-10-30 08:00:00', '2026-10-30 09:05:00', 'COMPLETED'),
(70, 39, '2026-10-30 09:30:00', '2026-10-30 10:35:00', 'CONFIRMED'),
(8, 40, '2026-10-30 13:00:00', '2026-10-30 14:05:00', 'CONFIRMED');
