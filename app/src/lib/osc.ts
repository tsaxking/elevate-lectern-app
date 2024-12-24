import { attemptAsync } from "./check";
import type { OscCommands } from "./events";
import { globals } from "./globals";
import { system } from "./stores/system";

export const send = <K extends keyof OscCommands>(command: K, data: OscCommands[K]) => {
    return attemptAsync(async () => {
        return fetch(`http://${__VITE_IP__}:4000/osc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command, data })
        }).then(res => res.json());
    });
}