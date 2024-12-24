import type { Show } from "./show";
import { type PresetConfig, type State } from "$lib/types";

export class Preset {
    public readonly id: number;
    public name: string;
    public state: State;
    
    constructor(data: PresetConfig, public readonly show: Show) {
        this.id = data.id;
        this.name = data.name;
        this.state = data.state;
    }

    json() {
        return {
            id: this.id,
            name: this.name,
            state: this.state
        };
    }
}