import jwt from 'jsonwebtoken';
export function auth(req,res,next){
 const header=req.headers.authorization;
 if(!header?.startsWith('Bearer ')) return res.status(401).json({error:'Please sign in to continue.'});
 try { req.user=jwt.verify(header.slice(7),process.env.JWT_SECRET); next(); }
 catch { return res.status(401).json({error:'Your session has expired. Please sign in again.'}); }
}
