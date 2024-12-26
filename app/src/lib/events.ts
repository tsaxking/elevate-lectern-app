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

export type OscCommands = {
    test: [1, 2, 3];
    move: number | string;
    stop: void;
    go_to: number;
    bump: number;
    preset: string;
};