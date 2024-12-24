<script lang="ts">
    import '$lib/imports.js';
	import { $Math as M } from "$lib/math.js";
    import { system } from "$lib/stores/system.js";
    import { send } from "$lib/osc.js";
	import { BootstrapColor } from "$lib/types.js";
    import State from "$lib/components/State.svelte";
	import OsInfo from "$lib/components/OSInfo.svelte";
    import { calibration } from '$lib/stores/calibration.js';


    const { data } = $props();
    const show = data.show;

    type Button = {
        name: string;
        action: () => void;
        color: BootstrapColor;
    }

    let motorSpeed = $state(0);
    let height = $state(0);

    let speedFocus = $state(true);
    let heightFocus = $state(true);

    let meMoving = $state(false);

    const buttons: Button[] = [
        {
            name: 'Small Bump Up',
            action: async () => {
                send('bump', .5);
            },
            color: BootstrapColor.PRIMARY
        }, {
            name: 'Small Bump Down',
            action: async () => {
                send('bump', -.5);
            },
            color: BootstrapColor.PRIMARY
        }, {
            name: 'Big Bump Up',
            action: async () => {
                send('bump', 1);
            },
            color: BootstrapColor.PRIMARY
        }, {
            name: 'Big Bump Down',
            action: async () => {
                send('bump', -1);
            },
            color: BootstrapColor.PRIMARY
        }, {
            name: 'Stop',
            action: () => {
                send('stop', undefined);
            },
            color: BootstrapColor.DANGER
        },
        ...$show.presets.map(p => ({
            name: p.name,
            action: () => {
                if (!confirm(`Go to ${p.name}?`)) return;
                // send('go_to', p.state.height);
                send('preset', show.id + '.' + p.id);
            },
            color: BootstrapColor.SECONDARY
        })),
        {
            name: 'Add Preset', 
            action: () => {
                const name = prompt('Enter Preset Name');
                if (!name) return;
                show.addPreset({
                    name,
                    state: {
                        height: $system.system.sensors.position
                    },
                    id: show.nextPresetId(),
                });
            },
            color: BootstrapColor.SUCCESS
        }
    ];

    const commit = () => {
        send('move', motorSpeed);
    };

    let timeout: NodeJS.Timeout;

    // onMount(() => {
    //     const i = setInterval(() => {
    //         if (motorSpeed) commit();
    //     }, 10);

    //     return () => clearInterval(i);
    // });
</script>

<pre>
{JSON.stringify($system, null, 4)}
{JSON.stringify($calibration, null, 4)}
</pre>

<div style="width: 100%; height: 300px;">
    <OsInfo />
</div>
<State />

{#if $system.connected}
    <div class="container">
        <div class="row">
            <div class="col-8">
                <div class="container-fluid">
                    <div class="row">
                        <label for="motor-speed-actual" class="form-label">Current Motor Speed: {M.roundTo(3, $system.system.motor_speed * 100)}%</label>
                        <input id="motor-speed-actual" type="range" class="form-control" min="{-1}" max="{1}" step="{0.001}" bind:value={$system.system.motor_speed} disabled={true}/>
                    </div>
                    <div class="row">
                        {#each buttons as button}
                            <div class="col-6 col-sm-4 col-md-3 col-lg-2 col-xl-1 my-2">
                                <button type="button" class="square w-100 btn btn-{button.color}" onclick={button.action}>
                                    {button.name}
                                </button>
                            </div>
                        {/each}
                    </div>
                    <div class="row">
                        <div class="col">
                            <div class="d-flex">
                                <span class="me-2"><i class="material-icons"></i></span>
                            </div>
                                <label for="motor-speed" class="form-label">Motor Control: {M.roundTo(3, motorSpeed * 100)}%</label>
                                <input id="motor-speed" type="range" class="form-control" min="{-1}" max="{1}" step="{0.001}" bind:value={motorSpeed} oninput={() => {
                                    clearTimeout(timeout);
                                    timeout = setTimeout(() => {
                                        commit();
                                    }, 20);
                                }} onchange={() => {
                                    send('stop', undefined);
                                    motorSpeed = 0;
                                }} />
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-4 h-100">
                <div class="container-fluid h-100">
                    <div class="row h-100">
                        <label for="height-actual" class="form-label">Current Height: {M.roundTo(3, $system.system.sensors.position)}cm</label>
                        <input id="height-actual" type="range" class="form-control" min="{0}" max="{100}" step="{0.001}" bind:value={$system.system.sensors.position} disabled={true}/>
                    </div>
                </div>
            </div>
        </div>
    </div>
{:else}
    <div class="container">
        <div class="row">
            <div class="col">
                <div class="card bg-danger">
                    <div class="card-body">
                        <h5 class="card-title">Not Connected</h5>
                        <p class="card-text">The system is not connected. Please ensure the control program is running properly</p>
                    </div> 
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .hidden {
        display: none;
    }

    .square {
        aspect-ratio: 1;
    }

    .vertical {
        transform: rotate(90deg);
        width: 1em;
        height: 1em;
    }
</style>