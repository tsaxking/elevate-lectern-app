import type { Writable } from "svelte/store";
import type { SystemState } from "../types";
import { listen } from "../sse";
import { globals } from "../globals";
import { nowSmall } from "../clock";

class System implements Writable<SystemState> {
    constructor(public state: SystemState) {}

    private readonly subscribers = new Set<(data: SystemState) => void>();

    set(data: SystemState) {
        this.state = data;
        this.subscribers.forEach(fn => fn(data));
    }

    update(fn: (data: SystemState) => SystemState) {
        this.set(fn(this.state));
    }

    subscribe(fn: (data: SystemState) => void) {
        this.subscribers.add(fn);
        fn(this.state);
        return () => {
            this.subscribers.delete(fn);
        }
    }
}

export const system = new System({
    os_info: {
        ip_address: '192.168.68.64',
        cpu_temp: NaN,
        cpu_usage: NaN,
        ram: NaN,
        updated: 0,
    },
    system: {
        motor_speed: NaN,
        target_speed: NaN,
        state: 'UNKNOWN',
        command_ready: false,
        gpio_moving: false,
        gpio_target_motor_speed: NaN,
        queue_length: NaN,
        target_pos: NaN,
        start_pos: NaN,
        velocity: NaN,
        motor_state: 'UNKNOWN',
        global_state: 'UNKNOWN',

        sensors: {
            position: NaN,
            power: false,
            main_up: false,
            main_down: false,
            secondary_up: false,
            secondary_down: false,
            main_speed: NaN,
            secondary_speed: NaN,
            min_limit: false,
            max_limit: false,
        }
    },
    connected: false,
});

listen('state', (state) => {
    // __VITE_IP__ = state.ip_address;
    system.set({
        os_info: {
            ...state.os_info,
            // updated: nowSmall(5).rebuild(state.os_info.updated).getTime(),
        },
        system: state.system ?? system.state.system,
        connected: !!state.system
    });
});
