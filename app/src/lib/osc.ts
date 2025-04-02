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

export const test = () => send("test", [1, 2, 3]);
export const move = (value: number | string) => send("move", value);
export const stop = () => send("stop", undefined);
export const goTo = (value: number | string) => send("go_to", value);
export const bump = (value: number | string) => send("bump", value);
export const preset = (value: string) => send("preset", value);
export const shutdown = () => send("shutdown", undefined);
export const calibrate = () => send("calibrate", undefined);
export const goToIn = (position: number, duration: number) => {
    return send("go_to_in", [position, duration]);
};