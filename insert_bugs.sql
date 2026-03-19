-- Reset + Insert Dummy Bugs (copy-paste into MySQL)
-- Make sure engineers with IDs 2 and 3 exist, or update engineer_id values.

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE Bug_Comments;
TRUNCATE TABLE ML_Analysis;
TRUNCATE TABLE Bug_stations;
TRUNCATE TABLE Bug_Tests;
TRUNCATE TABLE Bugs;

SET FOREIGN_KEY_CHECKS = 1;

-- Insert Repro Bugs
INSERT INTO Bugs (priority, bug_code, bug_type, engineer_id, summary, station_config, resource_group, status) VALUES
('P0', 'REPRO-2024-001', 'repro', 2, 'Critical application crash on startup', 'Config-A-Standard', 'Group-Alpha', 'pending'),
('P0', 'REPRO-2024-002', 'repro', 2, 'Security vulnerability in authentication flow', 'Config-B-Advanced', 'Group-Beta', 'running'),
('P1', 'REPRO-2024-003', 'repro', 3, 'Memory leak in data processing module', 'Config-C-Premium', 'Group-Alpha', 'pending'),
('P1', 'REPRO-2024-004', 'repro', 3, 'Database connection timeout under load', 'Config-A-Standard', 'Group-Gamma', 'scheduled'),
('P2', 'REPRO-2024-005', 'repro', 2, 'Performance degradation with large datasets', 'Config-D-Enterprise', 'Group-Beta', 'pending'),
('P2', 'REPRO-2024-006', 'repro', 3, 'UI rendering issue on high-resolution displays', 'Config-B-Advanced', 'Group-Delta', 'completed'),
('P3', 'REPRO-2024-007', 'repro', 2, 'Incorrect data validation in form submission', 'Config-E-Custom', 'Group-Alpha', 'pending'),
('P4', 'REPRO-2024-008', 'repro', 3, 'Minor text alignment issue in settings panel', 'Config-A-Standard', 'Group-Gamma', 'running');

-- Insert Test Bugs
INSERT INTO Bugs (priority, bug_code, bug_type, engineer_id, summary, station_config, resource_group, status) VALUES
('P0', 'TEST-2024-001', 'test', 2, 'Security penetration testing for API endpoints', 'Config-Test-1', 'Group-Alpha', 'pending'),
('P1', 'TEST-2024-002', 'test', 2, 'Load testing for concurrent user sessions', 'Config-Test-2', 'Group-Beta', 'scheduled'),
('P1', 'TEST-2024-003', 'test', 3, 'Performance benchmarking for database queries', 'Config-Test-3', 'Group-Alpha', 'pending'),
('P2', 'TEST-2024-004', 'test', 3, 'Integration testing with third-party services', 'Config-Test-1', 'Group-Gamma', 'running'),
('P2', 'TEST-2024-005', 'test', 2, 'Verify login functionality across browsers', 'Config-Test-4', 'Group-Beta', 'pending'),
('P3', 'TEST-2024-006', 'test', 3, 'Cross-platform compatibility testing', 'Config-Test-2', 'Group-Delta', 'completed'),
('P3', 'TEST-2024-007', 'test', 2, 'Test responsive design on mobile devices', 'Config-Test-5', 'Group-Alpha', 'pending'),
('P4', 'TEST-2024-008', 'test', 3, 'UI accessibility compliance testing', 'Config-Test-3', 'Group-Gamma', 'scheduled');

-- Insert Bug Tests (resolve bug_id from bug_code)
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Smoke Test' FROM Bugs WHERE bug_code = 'REPRO-2024-001';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Regression Test' FROM Bugs WHERE bug_code = 'REPRO-2024-001';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Security Test' FROM Bugs WHERE bug_code = 'REPRO-2024-002';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Penetration Test' FROM Bugs WHERE bug_code = 'REPRO-2024-002';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Performance Test' FROM Bugs WHERE bug_code = 'REPRO-2024-003';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Load Test' FROM Bugs WHERE bug_code = 'REPRO-2024-003';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Integration Test' FROM Bugs WHERE bug_code = 'REPRO-2024-004';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Unit Test' FROM Bugs WHERE bug_code = 'REPRO-2024-004';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'API Test' FROM Bugs WHERE bug_code = 'REPRO-2024-005';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'UI Test' FROM Bugs WHERE bug_code = 'REPRO-2024-005';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Regression Test' FROM Bugs WHERE bug_code = 'REPRO-2024-006';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Performance Test' FROM Bugs WHERE bug_code = 'REPRO-2024-006';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Smoke Test' FROM Bugs WHERE bug_code = 'REPRO-2024-007';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Integration Test' FROM Bugs WHERE bug_code = 'REPRO-2024-007';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Unit Test' FROM Bugs WHERE bug_code = 'REPRO-2024-008';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'API Test' FROM Bugs WHERE bug_code = 'REPRO-2024-008';

INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Security Test' FROM Bugs WHERE bug_code = 'TEST-2024-001';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'API Test' FROM Bugs WHERE bug_code = 'TEST-2024-001';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Load Test' FROM Bugs WHERE bug_code = 'TEST-2024-002';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Stress Test' FROM Bugs WHERE bug_code = 'TEST-2024-002';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Performance Test' FROM Bugs WHERE bug_code = 'TEST-2024-003';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Benchmark Test' FROM Bugs WHERE bug_code = 'TEST-2024-003';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Integration Test' FROM Bugs WHERE bug_code = 'TEST-2024-004';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'API Test' FROM Bugs WHERE bug_code = 'TEST-2024-004';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Functional Test' FROM Bugs WHERE bug_code = 'TEST-2024-005';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Smoke Test' FROM Bugs WHERE bug_code = 'TEST-2024-005';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Compatibility Test' FROM Bugs WHERE bug_code = 'TEST-2024-006';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Integration Test' FROM Bugs WHERE bug_code = 'TEST-2024-006';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'UI Test' FROM Bugs WHERE bug_code = 'TEST-2024-007';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Responsive Test' FROM Bugs WHERE bug_code = 'TEST-2024-007';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Accessibility Test' FROM Bugs WHERE bug_code = 'TEST-2024-008';
INSERT INTO Bug_Tests (bug_id, test_name) SELECT id, 'Compliance Test' FROM Bugs WHERE bug_code = 'TEST-2024-008';

-- Insert Bug Stations (resolve bug_id from bug_code)
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-A1' FROM Bugs WHERE bug_code = 'REPRO-2024-001';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-A2' FROM Bugs WHERE bug_code = 'REPRO-2024-001';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-B1' FROM Bugs WHERE bug_code = 'REPRO-2024-002';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-B2' FROM Bugs WHERE bug_code = 'REPRO-2024-002';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-B3' FROM Bugs WHERE bug_code = 'REPRO-2024-002';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-C1' FROM Bugs WHERE bug_code = 'REPRO-2024-003';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-C2' FROM Bugs WHERE bug_code = 'REPRO-2024-003';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-D1' FROM Bugs WHERE bug_code = 'REPRO-2024-004';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-D2' FROM Bugs WHERE bug_code = 'REPRO-2024-004';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-E1' FROM Bugs WHERE bug_code = 'REPRO-2024-005';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-E2' FROM Bugs WHERE bug_code = 'REPRO-2024-005';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-E3' FROM Bugs WHERE bug_code = 'REPRO-2024-005';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-F1' FROM Bugs WHERE bug_code = 'REPRO-2024-006';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-F2' FROM Bugs WHERE bug_code = 'REPRO-2024-006';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-G1' FROM Bugs WHERE bug_code = 'REPRO-2024-007';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-G2' FROM Bugs WHERE bug_code = 'REPRO-2024-007';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-H1' FROM Bugs WHERE bug_code = 'REPRO-2024-008';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Station-H2' FROM Bugs WHERE bug_code = 'REPRO-2024-008';

INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-1' FROM Bugs WHERE bug_code = 'TEST-2024-001';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-2' FROM Bugs WHERE bug_code = 'TEST-2024-001';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-3' FROM Bugs WHERE bug_code = 'TEST-2024-002';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-4' FROM Bugs WHERE bug_code = 'TEST-2024-002';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-5' FROM Bugs WHERE bug_code = 'TEST-2024-003';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-6' FROM Bugs WHERE bug_code = 'TEST-2024-003';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-7' FROM Bugs WHERE bug_code = 'TEST-2024-004';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-8' FROM Bugs WHERE bug_code = 'TEST-2024-004';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-9' FROM Bugs WHERE bug_code = 'TEST-2024-005';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-10' FROM Bugs WHERE bug_code = 'TEST-2024-005';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-11' FROM Bugs WHERE bug_code = 'TEST-2024-006';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-12' FROM Bugs WHERE bug_code = 'TEST-2024-006';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-13' FROM Bugs WHERE bug_code = 'TEST-2024-007';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-14' FROM Bugs WHERE bug_code = 'TEST-2024-007';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-15' FROM Bugs WHERE bug_code = 'TEST-2024-008';
INSERT INTO Bug_stations (bug_id, station_name) SELECT id, 'Test-Station-16' FROM Bugs WHERE bug_code = 'TEST-2024-008';