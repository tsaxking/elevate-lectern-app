import { browser } from "$app/environment";
import { attemptAsync, type Result } from "./check";
import { EventEmitter } from "./event-emitter";
import type { Events } from "./events";
import { globals } from "./globals";
import { decode } from "./text";

const emitter = new EventEmitter<Events>();

const init = (create: boolean) => {
    if (!create) return;

    const source = new EventSource('/sse');

    source.addEventListener('message', (event) => {
        const e = JSON.parse(decode(event.data));
        emitter.emit(e.event, e.data);
    });

    source.addEventListener('error', console.error);
    
    window.addEventListener('beforeunload', () => {
        source.close();
    });
};

init(browser);

export const listen = <K extends keyof Events>(event: K, cb: (data: Events[K]) => void) => {
    emitter.on(event, cb);

    return () => emitter.off(event, cb);
};

export const send = <K extends keyof Events>(event: K, data: Events[K]): Promise<Result<unknown>> => {
    return attemptAsync(async () => {
        return fetch(`http://${__VITE_HOST__}/sse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ event, data })
        }).then(res => res.json());
    });
};