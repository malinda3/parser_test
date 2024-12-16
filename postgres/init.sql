CREATE TABLE IF NOT EXISTS form_orders (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    user_id INT NOT NULL,
    username VARCHAR(255) NOT NULL,
    url TEXT NOT NULL
);
