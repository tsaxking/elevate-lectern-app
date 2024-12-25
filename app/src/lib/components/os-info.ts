import { Drawable } from "$lib/canvas/drawable";
import { Path } from "$lib/canvas/path";
import { type SystemState } from "$lib/types";


export class OSGraph extends Drawable {
    private readonly cpu_temp = new Path([]);
    private readonly cpu_usage = new Path([]);
    private readonly ram = new Path([]);
    // private readonly osc = new Path([]);
    constructor(private state: SystemState) {
        super();
    }

    updateState(state: SystemState) {
        this.state = state;
    }
}