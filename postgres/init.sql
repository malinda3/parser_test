CREATE TABLE IF NOT EXISTS form_orders (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    price VARCHAR(20) NOT NULL
);
