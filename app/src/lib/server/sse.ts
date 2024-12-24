import { encode } from '$lib/text';

const createMessageString = (event: string, data: unknown) => {
    return `data: ${encode(JSON.stringify({ event, data }))}\n\n`;
};

const createSSE = () => {
    const connections = new Set<ReadableStreamDefaultController<string>>();

    return {
        connect() {
            let _controller: ReadableStreamDefaultController<string>;

            return new ReadableStream({
                start(controller) {
                    _controller = controller;
                    connections.add(_controller);
                },
                cancel() {
                    connections.delete(_controller);
                }
            });
        },
        send(event: string, data: unknown) {
            const str = createMessageString(event, data);
            connections.forEach((controller) => controller.enqueue(str));
        }
    };
};

const sse = createSSE();

export default sse;