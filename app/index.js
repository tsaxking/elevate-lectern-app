import { handler } from './build/handler.js';
import express from 'express';
import http from 'http';


const server = http.createServer(handler);

const PORT = 80;
const HOSTNAME = 'taylorpi.local';


server.listen(PORT, HOSTNAME, () => {
	console.log(`Server running at http://${HOSTNAME}:${PORT}`);
});

// const app = express();

// // add a route that lives separately from the SvelteKit app
// app.get('/healthcheck', (req, res) => {

// 	res.end('ok');
// });

// // let SvelteKit handle everything else, including serving prerendered pages and static assets
// app.use(handler);

// app.listen(80, () => {
// 	console.log('listening on taylorpi.local');
// });