CREATE TABLE IF NOT EXISTS parsed_data (
    id SERIAL PRIMARY KEY,
    content TEXT,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
