import { type Writable } from "svelte/store";

type Config = {
    tickSpeed: number;
    step: number;
    tolerance: number;
}

export class Inc implements Writable<number> {
    private loop: NodeJS.Timeout | null = null;
    private target;

    constructor(public value: number, public profile: Config) {
        this.target = value;
    }

    start() {
        if (this.loop) return;
        this.loop = setInterval(() => {
            if (Math.abs(this.value - this.target) < this.profile.tolerance) return; // Stop if we're close enough

            if (this.value < this.target) {
                this.value += this.profile.step;
            } else {
                this.value -= this.profile.step;
            }

            // this.subscribers.forEach(fn => fn(this.value));
            this.set(this.value);
        }, this.profile.tickSpeed);
    }

    private readonly subscribers = new Set<(data: number) => void>();

    set(data: number) {
        this.target = data;
        this.subscribers.forEach(fn => fn(data));
    }

    update(fn: (data: number) => number) {
        this.set(fn(this.value));
    }

    subscribe(fn: (data: number) => void) {
        this.subscribers.add(fn);
        fn(this.value);
        return () => {
            this.subscribers.delete(fn);
        }
    }
}