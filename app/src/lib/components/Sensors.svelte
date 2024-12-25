<script lang="ts">
    import { system } from "$lib/stores/system";
	import Led from "./LED.svelte";
    import { Color } from "$lib/colors/color";
    import Range from "./Range.svelte";

    const { abs, log } = Math;

    const LED_SIZE = 12;

    // const blue = new Color(0, 200, 255).toString();
    const green = new Color(57, 255, 20).toString();
    const yellow = new Color(255, 255, 0).toString();
    const red = new Color(255, 72, 82).toString();


const determineColor = (number: number): string => {
    number = abs(number);
    if (number <= 10) return red;
    if (number < 20) return yellow;
    return green;
};

const determineStr = (number: number) => {
    number = abs(number);
    if (number <= 10) return 'Slowing Down';
    if (number < 20) return 'Approaching Limit';
    return 'Good';
};
</script>

<!-- <pre>
{JSON.stringify($system, null, 4)}
</pre> -->

{#snippet numLED(num: number)}
    <Led color={determineColor(num)} brightness={1-log(abs(num / 10))} size={LED_SIZE}/>
{/snippet}

{#snippet boolLED(bool: boolean)}
    <Led color={bool ? red : green} brightness={1} size={LED_SIZE}/>
{/snippet}

{#snippet potentiometer(num: number, min: number, max: number)}
    <Range value={num} {max} {min} step={.01} disabled={true}/>
{/snippet}

<div class="card p-0 shadow">
    <div class="card-header">
        <h5 class="card-title dashboard-title">Sensors</h5>
    </div>
    <div class="card-body sensors">
        <div class="container-fluid p-0">
            <div class="row p-0">
                <div class="col-8 p-0">
                    <ul class="list-group">
                        <li class="list-group-item d-flex align-items-center">
                            {@render numLED($system.system.proximity_up)}
                            <span class="ms-2" style="color: {determineColor($system.system.proximity_up)}">Upper Proximity: {determineStr($system.system.proximity_up)}</span>
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            {@render numLED($system.system.proximity_down)}
                            <span class="ms-2" style="color: {determineColor($system.system.proximity_down)}">Lower Proximity: {determineStr($system.system.proximity_down)}</span>
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            <span class="me-2">Main Speed</span>
                            {@render potentiometer($system.system.sensors.main_speed, 0, 1)}
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            <span class="me-2">Lectern Speed</span>
                            {@render potentiometer($system.system.sensors.secondary_speed, 0, 1)}
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            <span class="me-2">Velocity</span>
                            {@render potentiometer($system.system.velocity, -1, 1)}
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            <span class="me-2">Target Speed</span>
                            {@render potentiometer($system.system.target_speed, -1, 1)}
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            <span class="me-2">Position</span>
                            {@render potentiometer($system.system.sensors.position, 0,50)}
                        </li>
                    </ul>
                </div>
                <div class="col-4">
                    <ul class="list-group">
                        <li class="list-group-item d-flex align-items-center">
                            {@render boolLED($system.system.sensors.max_limit)}
                            <span class="ms-2">Upper Limit</span>
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            {@render boolLED($system.system.sensors.min_limit)}
                            <span class="ms-2">Lower Limit</span>
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            {@render boolLED($system.system.sensors.main_up)}
                            <span class="ms-2">Remote Up</span>
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            {@render boolLED($system.system.sensors.main_down)}
                            <span class="ms-2">Remote Down</span>
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            {@render boolLED($system.system.sensors.secondary_up)}
                            <span class="ms-2">Lectern Up</span>
                        </li>
                        <li class="list-group-item d-flex align-items-center">
                            {@render boolLED($system.system.sensors.secondary_down)}
                            <span class="ms-2">Lectern Down</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

    </div>
</div>

<style>
    .sensors {
        overflow-x: hidden;
    }
</style>