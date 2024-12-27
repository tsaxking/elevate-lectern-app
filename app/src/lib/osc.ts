import { attemptAsync } from "./check";
import type { OscCommands } from "./events";

export const send = <K extends keyof OscCommands>(command: K, data: OscCommands[K]) => {
    return attemptAsync(async () => {
        return fetch(`http://${__VITE_HOST__}/osc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command, data })
        }).then(res => res.json());
    });
}