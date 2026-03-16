-- Insert Dummy Bugs (Copy-paste this into MySQL terminal)
-- Make sure you have engineers with IDs 2, 3 or change the engineer_id values

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

-- Insert Bug Tests
INSERT INTO Bug_Tests (bug_id, test_name) VALUES
(9, 'Smoke Test'), (9, 'Regression Test'),
(10, 'Security Test'), (10, 'Penetration Test'),
(11, 'Performance Test'), (11, 'Load Test'),
(12, 'Integration Test'), (12, 'Unit Test'),
(13, 'API Test'), (13, 'UI Test'),
(14, 'Regression Test'), (14, 'Performance Test'),
(15, 'Smoke Test'), (15, 'Integration Test'),
(16, 'Unit Test'), (16, 'API Test'),
(17, 'Security Test'), (17, 'API Test'),
(18, 'Load Test'), (18, 'Stress Test'),
(19, 'Performance Test'), (19, 'Benchmark Test'),
(20, 'Integration Test'), (20, 'API Test'),
(21, 'Functional Test'), (21, 'Smoke Test'),
(22, 'Compatibility Test'), (22, 'Integration Test'),
(23, 'UI Test'), (23, 'Responsive Test'),
(24, 'Accessibility Test'), (24, 'Compliance Test');

-- Insert Bug Stations
INSERT INTO Bug_stations (bug_id, station_name) VALUES
(9, 'Station-A1'), (9, 'Station-A2'),
(10, 'Station-B1'), (10, 'Station-B2'), (10, 'Station-B3'),
(11, 'Station-C1'), (11, 'Station-C2'),
(12, 'Station-D1'), (12, 'Station-D2'),
(13, 'Station-E1'), (13, 'Station-E2'), (13, 'Station-E3'),
(14, 'Station-F1'), (14, 'Station-F2'),
(15, 'Station-G1'), (15, 'Station-G2'),
(16, 'Station-H1'), (16, 'Station-H2'),
(17, 'Test-Station-1'), (17, 'Test-Station-2'),
(18, 'Test-Station-3'), (18, 'Test-Station-4'),
(19, 'Test-Station-5'), (19, 'Test-Station-6'),
(20, 'Test-Station-7'), (20, 'Test-Station-8'),
(21, 'Test-Station-9'), (21, 'Test-Station-10'),
(22, 'Test-Station-11'), (22, 'Test-Station-12'),
(23, 'Test-Station-13'), (23, 'Test-Station-14'),
(24, 'Test-Station-15'), (24, 'Test-Station-16');