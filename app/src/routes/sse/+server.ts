import type { Events } from '$lib/events.js';
import sse from '$lib/server/sse';
import { Show } from '$lib/server/show.js';
import type { ShowConfig } from '$lib/types.js';
import '$lib/server/udp.js';

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	const body = sse.connect();

	const headers = {
		'cache-control': 'no-store',
		'content-type': 'text/event-stream'
	};

	return new Response(body, { headers });
}

export async function POST(request) {
	const body = await request.request.json();
	const { event, data } = body as {
		event: keyof Events;
		data: Events[keyof Events];
	};

	switch (event) {
		case 'deleteShow':
			Show.open(data as number).then(async s => {
				if (s.isOk()) (await s.value.delete()).unwrap();
			});
			break;
		case 'updateShow':
			Show.open((data as ShowConfig).id).then(async s => {
				if (s.isOk()) {
					(await s.value.update(data as ShowConfig)).unwrap();
				}
			});
			break;
		case 'newShow':
			Show.new(data as ShowConfig);
		case 'getAllShows':
			return new Response(JSON.stringify((await Show.getShows()).unwrap().map(s => s.json())), {
				headers: {
					'content-type': 'application/json'
				},
				status: 200
			});
		case 'openShow':
			return new Response(JSON.stringify((await Show.open(data as number)).unwrap().json()), {
				headers: {
					'content-type': 'application/json'
				},
				status: 200
			});
	}


	return new Response(null, {
		status: 200
	})
}