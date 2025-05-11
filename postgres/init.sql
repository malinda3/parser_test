CREATE TABLE IF NOT EXISTS parsed_data (
    id SERIAL PRIMARY KEY,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
