import type { Writable } from "svelte/store";
import type { Calibration as C } from "$lib/types";
import { listen } from "$lib/sse";

class Calibration implements Writable<C> {
    constructor(public state: C) {}

    private readonly subscribers = new Set<(data: C) => void>();

    set(data: C) {
        this.state = data;
        this.subscribers.forEach(fn => fn(data));
    }

    update(fn: (data: C) => C) {
        this.set(fn(this.state));
    }

    subscribe(fn: (data: C) => void) {
        this.subscribers.add(fn);
        fn(this.state);
        return () => {
            this.subscribers.delete(fn);
        }
    }
}

export const calibration = new Calibration({
    top: NaN,
    bottom: NaN,
    velocity: NaN,
    i_am: 'calibration'
});

listen('calibration', c => calibration.set(c));