import { type Writable, writable } from "svelte/store";
import { listen, send } from "../sse";
import type { ShowConfig, PresetConfig } from "../types";
import { attemptAsync } from "../check";


export const shows = writable<Show[]>([]);

export class Show implements Writable<ShowConfig> {
    public static getAll() {
        (async () => {
            attemptAsync(async () => {
                const s = (await send('getAllShows', undefined)).unwrap();
                return (s as ShowConfig[]).map(s => new Show(s));
            });
        })();
        return shows;
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
    constructor(config: ShowConfig) {
        this.id = config.id;
        this.name = config.name;
        // this.presets = config.presets.map(p => new Preset(p, this));
        this.presets = config.presets;

        shows.update(s => [
            ...s,
            this
        ].filter((v, i, a) => a.findIndex(v2 => v2.id === v.id) === i));
    }

    private readonly subscribers = new Set<(data: ShowConfig) => void>();

    set(data: ShowConfig) {
        this.name = data.name;
        this.presets = data.presets;
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
        })
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
            presets: this.presets
        };
    }

    nextPresetId() {
        return Math.max(...this.presets.map(p => p.id), 0) + 1;
    }
}

listen('newShow', (data) => {
    new Show(data);
});

listen('updateShow', (data) => {
    shows.update(s => s.map(s => {
        if (s.id === data.id) s.set(data);
        return s;
    }));
});

listen('deleteShow', (id) => {
    shows.update(s => s.filter(s => s.id !== id));
});