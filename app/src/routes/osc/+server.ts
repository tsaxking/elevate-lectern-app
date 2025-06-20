import { sendOSC } from '$lib/server/osc';


export const POST = async (event) => {
    const { command } = await event.request.json();
    
    sendOSC(command);

    return new Response(null, {
        status: 200
    });
};