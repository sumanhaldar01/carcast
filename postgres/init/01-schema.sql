CREATE TABLE users (
 id SERIAL PRIMARY KEY, name VARCHAR(80) NOT NULL, email VARCHAR(255) UNIQUE NOT NULL,
 password_hash TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE products (
 id SERIAL PRIMARY KEY, slug VARCHAR(100) UNIQUE NOT NULL, name VARCHAR(120) NOT NULL,
 category VARCHAR(30) NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
 description TEXT NOT NULL, color VARCHAR(30) NOT NULL, image_key VARCHAR(40) NOT NULL, featured BOOLEAN DEFAULT false
);
CREATE TABLE carts (id SERIAL PRIMARY KEY, user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE);
CREATE TABLE cart_items (cart_id INTEGER REFERENCES carts(id) ON DELETE CASCADE, product_id INTEGER REFERENCES products(id), quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 20), PRIMARY KEY(cart_id,product_id));
CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), invoice_no VARCHAR(30) UNIQUE NOT NULL, total_cents INTEGER NOT NULL, status VARCHAR(30) NOT NULL DEFAULT 'paid_demo', created_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE order_items (id SERIAL PRIMARY KEY, order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE, product_id INTEGER REFERENCES products(id), name VARCHAR(120) NOT NULL, quantity INTEGER NOT NULL, unit_price_cents INTEGER NOT NULL);
INSERT INTO products(slug,name,category,price_cents,description,color,image_key,featured) VALUES
('sunset-racer','Sunset Racer','Cars',1899,'A pocket-sized retro coupe with a smooth metal body and sunny finish.','Coral','racer',true),
('mint-gt','Mint GT','Cars',2299,'Low-profile grand tourer with crisp details and free-rolling wheels.','Mint','gt',true),
('night-rally','Night Rally','Cars',1999,'Built for imaginary midnight stages, with a bold roof light bar.','Navy','rally',true),
('little-hauler','Little Hauler','Trucks',1699,'A cheerful mini cargo truck ready for a shelf or playroom route.','Yellow','truck',false),
('space-orbit','Space Orbit','Toys',2499,'A friendly wooden-style explorer toy for faraway adventures.','Lilac','space',true),
('pit-crew-set','Pit Crew Set','Sets',3299,'Four tiny accessories to build a complete race-day story.','Peach','pit',false);
