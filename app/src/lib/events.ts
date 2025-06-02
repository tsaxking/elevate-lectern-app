import type { ShowConfig, SystemState, Calibration } from "./types";

export type Events = {
    connect: void;
    disconnect: void;
    keepalive: void;
    updateShow: ShowConfig;
    deleteShow: number;
    newShow: ShowConfig;
    getAllShows: void;
    openShow: number;
    state: SystemState;
    calibration: Calibration;
};

// export type OscCommands = {
//     test: [1, 2, 3];
//     move: number | string;
//     stop: void;
//     go_to: number | string;
//     bump: number | string;
//     preset: string;
//     shutdown: void;
//     calibrate: void;
//     go_to_in: [number, number];
// };

export type OscCommand = 
    '/test' |
    `/move/${number}` |
    '/stop' |
    `/go_to/${number}` |
    `/go_to/${number}/in/${number}` |
    `/bump/${number}` |
    '/lectern/test' |
    `/lectern/move/${number}` |
    '/lectern/stop' |
    `/lectern/go_to/${number}` |
    `/lectern/bump/${number}` |
    '/lectern/calibrate' |
    `/lectern/go_to/${number}/in/${number}` |
    `/teleprompter/${string}/bump/${number}` |
    `/teleprompter/${string}/move/${number}` |
    `/teleprompter/${string}/stop` |
    `/teleprompter/${string}/go_to/${number}` |
    `/teleprompter/${string}/go_to/${number}/in/${number}`;

export type TCPCommand = 
    '/stop' | 
    '/lectern/stop' |
    `/teleprompter/${string}/stop` |
    '/reboot' |
    '/lectern/reboot' |
    `/teleprompter/${string}/reboot` |
    '/home' |
    '/lectern/home' |
    `/teleprompter/${string}/home` |
    '/system_reboot' |
    '/reboot_tcp' |
    '/reboot_osc' |
    `/lectern/manual_speed/${number}` |
    '/shutdown';