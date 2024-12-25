import { attemptAsync, resolveAll } from "$lib/check";
import { getJSON, saveJSON, getJSONS, deleteJSON } from "./utils";
import type { ShowConfig, PresetConfig } from "$lib/types";
import sse from "./sse";


export class Show {
    public static open(id: number) {
        return attemptAsync(async () => {
            const data = await getJSON<ShowConfig>(`show-${id}`);
            return new Show(data.unwrap());
        });
    }

    public static getShows() {
        return attemptAsync(async () => {
            const files = (await getJSONS()).unwrap();
            return resolveAll(await Promise.all(
                files.map(async file => {
                    const id = parseInt(file.replace('show-', '').replace('.json', ''));
                    return Show.open(id);
                })
            )).unwrap();
        });
    }

    public static new(data: Omit<ShowConfig, 'id'>) {
        return attemptAsync(async () => {
            const files = (await getJSONS()).unwrap();
            const id = Math.max(...files.map(file => parseInt(file.replace('show-', '').replace('.json', ''))), 0) + 1;
            const show = new Show({ ...data, id });
            await show.save(false);
            sse.send('newShow', show.json());
            return show;
        });
    }

    public readonly id: number;
    public name: string;
    public presets: PresetConfig[];
    public color: string;
    
    constructor(data: ShowConfig) {
        this.id = data.id;
        this.name = data.name;
        // this.presets = data.presets.map(p => new Preset(p, this));
        this.presets = data.presets;
        this.color = data.color;
    }

    addPreset(preset: PresetConfig) {
        return attemptAsync(async () => {
            this.presets.push(preset);
            this.save(true);
        });
    }

    removePreset(id: number) {
        return attemptAsync(async () => {
            this.presets = this.presets.filter(p => p.id !== id);
            this.save(true);
        });
    }

    save(emit: boolean) {
        if (emit) sse.send('updateShow', this.json());
        return saveJSON(`show-${this.id}`, this);
    }

    json(): ShowConfig {
        return {
            id: this.id,
            name: this.name,
            presets: this.presets,
            color: this.color,
        };
    }

    update(data: ShowConfig) {
        this.name = data.name;
        this.presets = data.presets.map(p => p);
        this.color = data.color;
        return this.save(true);
    }

    delete() {
        sse.send('deleteShow', this.id);
        return deleteJSON(`show-${this.id}`);
    }
}