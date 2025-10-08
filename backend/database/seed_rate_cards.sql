INSERT INTO rate_cards (category, item_name, unit, base_rate, overtime_rate, is_default) VALUES
('Talent', 'Principal Actor', 'per day', 950.00, 142.50, TRUE),
('Talent', 'Supporting Actor', 'per day', 650.00, 97.50, TRUE),
('Talent', 'Background Performer', 'per day', 180.00, 27.00, TRUE),
('Crew', 'Director of Photography', 'per day', 1200.00, 180.00, TRUE),
('Crew', 'Assistant Director', 'per day', 850.00, 127.50, TRUE),
('Crew', 'Gaffer', 'per day', 550.00, 82.50, TRUE),
('Equipment', 'Camera Package', 'per day', 750.00, 0.00, TRUE),
('Equipment', 'Lighting Package', 'per day', 480.00, 0.00, TRUE),
('Logistics', 'Company Move', 'per move', 350.00, 0.00, TRUE),
('Logistics', 'Permit Fees', 'per day', 275.00, 0.00, TRUE),
('Misc', 'Catering', 'per person', 32.00, 0.00, TRUE),
('Misc', 'Craft Services', 'per day', 150.00, 0.00, TRUE)
ON CONFLICT DO NOTHING;

