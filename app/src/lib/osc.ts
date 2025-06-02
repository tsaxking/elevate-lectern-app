import { attemptAsync } from "./check";
import type { OscCommand } from "./events";

export const send = <K extends OscCommand>(command: K) => {
    return attemptAsync(async () => {
        return fetch(`http://${__VITE_HOST__}/osc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command })
        }).then(res => res.json());
    });
}
export namespace All {
    export const test = () => send('/test');
    export const move = (value: number) => send(`/move/${value}`);
    export const stop = () => send('/stop');
    export const goTo = (value: number) => send(`/go_to/${value}`);
    export const bump = (value: number) => send(`/bump/${value}`);
    // export const preset = (value: string) => send(`/preset/${value}`);
    export const goToIn = (position: number, duration: number) => {
        return send(`/go_to/${position}/in/${duration}`);
    }


    export namespace Lectern {
        export const test = () => send('/lectern/test');
        export const move = (value: number) => send(`/lectern/move/${value}`);
        export const stop = () => send('/lectern/stop');
        export const goTo = (value: number) => send(`/lectern/go_to/${value}`);
        export const bump = (value: number) => send(`/lectern/bump/${value}`);
        export const calibrate = () => send('/lectern/calibrate');
        export const goToIn = (position: number, duration: number) => {
            return send(`/lectern/go_to/${position}/in/${duration}`);
        }
    }

    export namespace Teleprompter {
        export const bump = (name: string, value: number) => send(`/teleprompter/${name}/bump/${value}`);
        export const move = (name: string, value: number) => send(`/teleprompter/${name}/move/${value}`);
        export const stop = (name: string) => send(`/teleprompter/${name}/stop`);
        export const goTo = (name: string, value: number) => send(`/teleprompter/${name}/go_to/${value}`);
        export const goToIn = (name: string, position: number, duration: number) => {
            return send(`/teleprompter/${name}/go_to/${position}/in/${duration}`);
        }
    }
}