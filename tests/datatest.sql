INSERT INTO users (username, password) VALUES
    ('user','pbkdf2:sha256:260000$D22gUT8HP7SkSasT$cd2ad68cc2ce9ff0af9346aadb3bd49f108338f80837c3130a3fff8a5dd0c2d7'),
    ('userother', 'pbkdf2:sha256:260000$c2XINgbdv0BZlzyj$cef30fa7e2bdf43d83d419c632335cb508dc6b1bd49d9ee47f54b860ddff4ccd');
INSERT INTO post (title, body, author_id, created) VALUES ('example title', 'example' || x'0a' || 'body', 1, '2022-11-26 00:00:00');