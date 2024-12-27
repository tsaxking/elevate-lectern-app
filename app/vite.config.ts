import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 4000,
		// host: 'taylorpi.local'
		// host: ip
		host: 'taylorpi.local'
	},
	define: {
		__VITE_HOST__: JSON.stringify(`taylorpi.local`)
	}
});
