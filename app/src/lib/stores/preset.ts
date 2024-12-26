import type { Show } from "./show.svelte";
import type { PresetConfig, State } from "../types";




export class Preset {
    public readonly id: number;
    public name: string;
    public state: State;
    constructor(config: PresetConfig, public readonly show: Show) {
        this.id = config.id;
        this.name = config.name;
        this.state = config.state;
    }

}