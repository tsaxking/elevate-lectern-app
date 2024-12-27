<script lang="ts">
    import { system } from "$lib/stores/system";
	import Led from "./LED.svelte";
    import { Color } from "$lib/colors/color";
    import Range from "./Range.svelte";

    const { abs, log } = Math;

    const LED_SIZE = 12;

    // const blue = new Color(0, 200, 255).toString();
    // const green = new Color(57, 255, 20).toString();
    // const yellow = new Color(255, 255, 0).toString();
    // const red = new Color(255, 72, 82).toString();

    const green = Color.fromHex('#63b57a').toString();
    const yellow = Color.fromHex('ffbf47').toString();
    const red = Color.fromHex('#e74c3c').toString();


const determineColor = (number: number): string => {
    number = abs(number);
    if (number <= 4) return red;
    if (number < 8) return yellow;
    return green;
};

const determineStr = (number: number) => {
    number = abs(number);
    if (number <= 4) return 'Slowing Down';
    if (number < 8) return 'Approaching Limit';
    return 'Good';
};
</script>

{#snippet numLED(num: number)}
    <Led color={determineColor(num)} brightness={1-log(abs(num / 10))} size={LED_SIZE}/>
{/snippet}

{#snippet boolLED(bool: boolean)}
    <Led color={bool ? red : green} brightness={1} size={LED_SIZE}/>
{/snippet}

{#snippet potentiometer(num: number, min: number, max: number)}
    <Range value={num} {max} {min} step={.01} disabled={true} vertical={true} style="width: 16px; height: 225px;" />
{/snippet}

<div class="card p-0 glow">
    <div class="card-header">
        <h5 class="card-title dashboard-title">Sensors</h5>
    </div>
    <div class="card-body sensors">
        <div class="container-fluid p-0">
            <div class="row p-0">
                <!-- <div class="col-3 p-0 h-100">
                    <ul class="list-group h-100">
                        <li class="list-group-item h-100 d-flex flex-column justify-content-center p-1" style="height: 329px !important;">
                            <p class="text-center">
                                Position
                            </p>
                            <p class="text-center">
                                ({$system.system.sensors.position}in)
                            </p>
                            <div class="w-100 d-flex justify-content-center">
                                {@render potentiometer($system.system.sensors.position, $system.system.calibration.bottom || 0, $system.system.calibration.top || 20)}
                            </div>
                        </li>
                    </ul>
                </div> -->
                <!-- <div class="col-9"> -->
                <div class="col-12">
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