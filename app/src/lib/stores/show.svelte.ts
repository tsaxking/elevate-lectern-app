import { type Writable, writable } from "svelte/store";
import { listen, send } from "../sse";
import type { ShowConfig, PresetConfig } from "../types";
import { attemptAsync, type Result } from "../check";


class ShowArr implements Writable<Show[]> {
    public readonly shows: Show[] = [];
    private readonly subscribers = new Set<(data: Show[]) => void>();

    constructor(data: Show[]) {
        this.shows.push(...data);
    }

    set(data: Show[]) {
        this.shows.splice(0, this.shows.length, ...data);
        this.subscribers.forEach(fn => fn(data));
    }

    update(fn: (data: Show[]) => Show[]) {
        this.set(fn(this.shows));
    }

    subscribe(fn: (data: Show[]) => void) {
        fn(this.shows);
        this.subscribers.add(fn);
        return () => this.subscribers.delete(fn);
    }

    // await() {
    //     return new Promise<Show[]>((res, rej) => {
    //         let resolved = false;
    //         const resolve = (data: Show[]) => {
    //             if (!resolved) {
    //                 resolved = true;
    //                 res(data);
    //             }
    //         }
            
    //         const u = this.subscribe(resolve);

    //         setTimeout(() => {
    //             if (!resolved) {
    //                 console.log('Timeout');
    //                 resolved = true;
    //                 rej("Timeout");
    //                 u();
    //             }
    //         }, 1000 * 10);
    //     });
    // }
}

const shows: Show[] = $state([]);


export class Show implements Writable<ShowConfig> {
    public static getAll(asWritable: false): Promise<Result<Show[]>>;
    public static getAll(asWritable: true): Show[];
    public static getAll(asWritable: boolean): Promise<Result<Show[]>> | Show[] {
        if (asWritable) {
            (async () => {
                attemptAsync(async () => {
                    if (shows.length) return;
                    const s = (await send('getAllShows', undefined)).unwrap();
                    const allShows = (s as ShowConfig[]).map(s => new Show(s));
                    shows.push(...allShows);
                });
            })();
            return shows;
        } else {
            return attemptAsync(async () => {
                const s = (await send('getAllShows', undefined)).unwrap();
                return (s as ShowConfig[]).map(s => new Show(s));
            });
        }
    }

    public static new(data: Omit<ShowConfig, 'id'>) {
        return attemptAsync(async () => {
            const s = (await send('newShow', {...data, id: -1})).unwrap();
            return new Show(s as ShowConfig);
        });
    }

    public static open(id: number) {
        return attemptAsync(async () => {
            const s = (await send('openShow', id)).unwrap();
            return new Show(s as ShowConfig);
        });
    }

    public readonly id: number;
    public name: string;
    public presets: PresetConfig[];
    public color: string;
    constructor(config: ShowConfig) {
        this.id = config.id;
        this.name = config.name;
        this.color = config.color;
        // this.presets = config.presets.map(p => new Preset(p, this));
        this.presets = config.presets;

        // shows.update(s => [
        //     ...s,
        //     this
        // ].filter((v, i, a) => a.findIndex(v2 => v2.id === v.id) === i));
    }

    private readonly subscribers = new Set<(data: ShowConfig) => void>();

    set(data: ShowConfig) {
        this.name = data.name;
        this.presets = data.presets;
        this.color = data.color;
        this.subscribers.forEach(fn => fn(data));
    }

    update(fn: (data: ShowConfig) => ShowConfig) {
        this.set(fn(this));
    }

    subscribe(fn: (data: ShowConfig) => void) {
        fn(this);
        this.subscribers.add(fn);
        return () => this.subscribers.delete(fn);
    }

    addPreset(preset: PresetConfig) {
        this.set({
            ...this,
            presets: [...this.presets, preset],
        });
        this.save();
    }

    removePreset(id: number) {
        this.update(s => ({ ...s, presets: s.presets.filter(p => p.id !== id) }));
    }

    save() {
        return send('updateShow', this.json());
    }

    json(): ShowConfig {
        return {
            id: this.id,
            name: this.name,
            presets: this.presets,
            color: this.color,
        };
    }

    nextPresetId() {
        return Math.max(...this.presets.map(p => p.id), 0) + 1;
    }

    delete() {
        return send('deleteShow', this.id);
    }
}

listen('newShow', (data) => {
    console.log('Received new show', data);
    const show = new Show(data);
    shows.push(show);
    // shows.update(s => [...s, show]);
});

listen('updateShow', (data) => {
    // shows.update(s => s.map(s => {
    //     if (s.id === data.id) s.set(data);
    //     return s;
    // }));
    shows.find(s => s.id === data.id)?.set(data);
});

listen('deleteShow', (id) => {
    // shows.update(s => s.filter(s => s.id !== id));
    shows.splice(shows.findIndex(s => s.id === id), 1);
});