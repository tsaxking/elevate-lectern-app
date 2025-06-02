import { sendTCP } from "$lib/server/osc";

export const POST = async (event) => {
    const { command } = await event.request.json();
    
    sendTCP(command);

    return new Response(null, {
        status: 200
    });
};