INSERT INTO element_categories (category_name, display_order, description, color) VALUES
('Cast', 1, 'Principal and supporting cast members', '#BFDBFE'),
('Extras', 2, 'Background performers and crowd requirements', '#C4B5FD'),
('Props', 3, 'Hand props and hero props required on set', '#FBCFE8'),
('Set Dressing', 4, 'Set dressing items and decor elements', '#FDE68A'),
('Wardrobe', 5, 'Wardrobe, costumes, and accessories', '#FCA5A5'),
('Makeup & Hair', 6, 'Makeup, hair, and prosthetic requirements', '#FBD38D'),
('Vehicles & Animals', 7, 'Vehicles, animals, and transportation needs', '#A7F3D0'),
('Sound FX', 8, 'Sound effects and audio playback cues', '#BBF7D0'),
('Special Effects', 9, 'Practical or digital special effects', '#FDBA74'),
('Stunts', 10, 'Stunts and stunt performer requirements', '#FECACA'),
('General', 11, 'Miscellaneous or uncategorized elements', '#E5E7EB')
ON CONFLICT (category_name) DO NOTHING;
