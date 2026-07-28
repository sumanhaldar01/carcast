import {pool} from '../db.js';
export async function cartFor(userId){
 await pool.query('INSERT INTO carts(user_id) VALUES($1) ON CONFLICT(user_id) DO NOTHING',[userId]);
 const {rows}=await pool.query(`SELECT ci.product_id as "productId",ci.quantity,p.name,p.price_cents as "priceCents",p.image_key as "imageKey" FROM carts c JOIN cart_items ci ON ci.cart_id=c.id JOIN products p ON p.id=ci.product_id WHERE c.user_id=$1 ORDER BY p.id`,[userId]);
 return rows;
}
