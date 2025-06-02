import type { TCPCommand } from "./events";

const send = <K extends TCPCommand>(command: K) => {
    return fetch(`http://${__VITE_HOST__}/tcp`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command })
    }).then(res => res.json());
}


export namespace All {
    export const stop = () => send('/stop');
    export const reboot = () => send('/reboot');
    export const home = () => send('/home');
    export const systemReboot = () => send('/system_reboot');
    export const rebootTCP = () => send('/reboot_tcp');
    export const rebootOSC = () => send('/reboot_osc');
    export const shutdown = () => send('/shutdown');

    export namespace Lectern {
        export const stop = () => send('/lectern/stop');
        export const reboot = () => send('/lectern/reboot');
        export const home = () => send('/lectern/home');
    }
    export namespace Teleprompter {
        export const stop = (name: string) => send(`/teleprompter/${name}/stop`);
        export const reboot = (name: string) => send(`/teleprompter/${name}/reboot`);
        export const home = (name: string) => send(`/teleprompter/${name}/home`);
    }
}