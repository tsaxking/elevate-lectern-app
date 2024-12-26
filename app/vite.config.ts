import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { getIp } from './src/lib/server/utils';

const ip = getIp().unwrap();

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 4000,
		// host: 'taylorpi.local'
		// host: ip
		host: 'taylorpi.local'
	},
	define: {
		__VITE_IP__: JSON.stringify('taylorpi.local')
	}
});
