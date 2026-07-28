INSERT INTO products(slug,name,category,price_cents,description,color,image_key,featured) VALUES
('blush-beetle','Blush Beetle','Cars',1799,'A curvy little city car in a soft pink finish, made for slow Sunday drives.','Blush','racer',false),
('forest-4x4','Forest 4×4','Cars',2799,'A sturdy off-road miniature with an explorer spirit and chunky wheels.','Sage','rally',true),
('coastal-cabriolet','Coastal Cabriolet','Cars',2399,'Top-down cruising in a breezy seafoam colourway.','Seafoam','gt',false),
('golden-delivery','Golden Delivery','Trucks',1899,'A sunny delivery van for parcels, picnics and pretend play.','Golden','truck',false),
('moon-rover','Moon Rover','Toys',2899,'A friendly lunar explorer toy, ready for crater-sized adventures.','Lavender','space',true),
('garage-day-set','Garage Day Set','Sets',3699,'A playful workshop set with miniature details for a full pit-stop scene.','Terracotta','pit',false)
ON CONFLICT (slug) DO NOTHING;
