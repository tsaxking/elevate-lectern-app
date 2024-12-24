import { send } from '$lib/server/osc';


send('test', [1, 2, 3]);


export const POST = async (event) => {
    const { command, data } = await event.request.json();
    
    send(command, data);

    return new Response(null, {
        status: 200
    });
};