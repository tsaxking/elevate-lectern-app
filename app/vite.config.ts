import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 8080,
		// host: 'localhost'
		// host: ip
		host: 'localhost'
	},
	define: {
		__VITE_HOST__: JSON.stringify(`taylorpi.local`)
	}
});
