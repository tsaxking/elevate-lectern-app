<script lang="ts">
	import { Show } from "$lib/stores/show.svelte";
    import { system } from "$lib/stores/system";
	import { BootstrapColor, type PresetConfig } from "$lib/types.js";
    import { send } from "$lib/osc.js";
    import Modal from "./Modal.svelte";
    import { goto } from "$app/navigation";
	import { confirm, prompt, select } from "$lib/prompts.svelte";
	import { $Math as M } from "$lib/math";


    interface Props {
        show: Show;
    }

    let { show = $bindable() }: Props = $props();

    // $inspect(show);

    type Button = {
        name: string;
        action: () => void;
        color: BootstrapColor;
        disabled: boolean;
        contextmenu?: (e: Event) => void;
    };

    
    const buttons: Button[] = $derived([{
            name: 'Stop',
            action: () => {
                send('stop', undefined);
            },
            color: BootstrapColor.DANGER,
            disabled: !$system.connected,
        },
        {
            name: 'Small Bump Up',
            action: async () => {
                send('bump', .5);
            },
            color: BootstrapColor.PRIMARY,
            disabled: !$system.connected,
        }, {
            name: 'Small Bump Down',
            action: async () => {
                send('bump', -.5);
            },
            color: BootstrapColor.PRIMARY,
            disabled: !$system.connected,
        }, {
            name: 'Big Bump Up',
            action: async () => {
                send('bump', 1);
            },
            color: BootstrapColor.PRIMARY,
            disabled: !$system.connected,
        }, {
            name: 'Big Bump Down',
            action: async () => {
                send('bump', -1);
            },
            color: BootstrapColor.PRIMARY,
            disabled: !$system.connected,
        }, 
        ...$show.presets.map(p => ({
            name: p.name,
            action: async () => {
                if (!await confirm(`Go to ${p.name}?`)) return;
                // send('go_to', p.state.height);
                send('preset', show.id + '.' + p.id);
            },
            color: BootstrapColor.SECONDARY,
            disabled: !$system.connected,
            contextmenu: (e: Event) => {
                e.preventDefault();
                currentPreset = p;
                modal.show();
            },
        })),
        {
            name: 'Add Preset', 
            action: async () => {
                const name = await prompt('Enter Preset Name');
                if (!name) return;
                show.addPreset({
                    name,
                    state: {
                        height: $system.system.sensors.position
                    },
                    id: show.nextPresetId(),
                });
            },
            color: BootstrapColor.SUCCESS,
            disabled: false,
        },
        {
            name: 'Change Show',
            action: async () => {
                const shows = (await Show.getAll(false)).unwrap();
                const selected = await select('Select Show', shows, {
                    render: s => s.name,
                });
                if (!selected) return;
                goto(`/show/${selected.id}/dashboard`, {
                    'replaceState': true,
                });
                show = selected;
            },
            color: BootstrapColor.INFO,
            disabled: false,
        },
        {
            name: 'Calibrate',
            action: async () => {
                if (await confirm('Run calibration? (This will lock the system until the calibration is complete)')) {
                    send('calibrate', undefined)
                }
            },
            color: BootstrapColor.WARNING,
            disabled: !$system.connected,
        },
        {
            name: 'Shutdown',
            action: async () => {
                if (await confirm('Shut down?')) {
                    send('shutdown', undefined);
                }
            },
            color: BootstrapColor.DANGER,
            disabled: !$system.connected,
        }
    ]);

    let motorSpeed = $state(0);
    const commitSpeed = () => {
        send('move', motorSpeed.toFixed(3));
    };

    let speedTimeout: NodeJS.Timeout;

    let posTimeout: NodeJS.Timeout;
    let pos = $state(0);
    let writingPos = $state(false);

    $effect(() => {
        if (writingPos) return;
        pos = $system.system.sensors.position;
    });

    const commitPos = () => {
        send('go_to', pos.toFixed(3));
    };

    let modal: Modal;
    let currentPreset: PresetConfig | null = $state(null);
</script>

<div class="card p-0 glow h-100">
    <div class="card-header">
        <h5 class="card-title dashboard-title">System Control</h5>
    </div>
    <div class="card-body p-0 system-controller h-100">
        <div class="container-fluid">
            <div class="row">
                <div class="col-2">
                    <h6 class="text-center ws-nowrap">Set Speed:</h6>
                    <small class="text-center ws-nowrap text-muted">{Math.round((motorSpeed || $system.system.motor_speed) * 100)}%</small>
                    <div class="d-flex justify-content-center">
                    <input type="range" id="motor-speed" class="form-range vertical" min={-1} max={1} step={.001} bind:value={motorSpeed} oninput={() => {
                        if (speedTimeout) clearTimeout(speedTimeout);
                        speedTimeout = setTimeout(commitSpeed, 20);
                    }} onchange={() => {
                        send('stop', undefined);
                        motorSpeed = 0;
                    }} 
                        style="
                            width: 16px;
                            height: 400px;
                        "
                    >
                    </div>
                </div>
                <div class="col-6">
                    <div class="container-fluid p-0">
                        <div class="row">
                            {#each buttons as button}
                                <div class="col-12">
                                    <button type="button" class="btn w-100 my-2 btn-{button.color}" onclick={button.action} disabled={button.disabled} oncontextmenu="{button.contextmenu}">
                                        {button.name}
                                    </button>
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>
                <div class="col-2">
                    <h6 class="text-center ws-nowrap">Set Pos:</h6>
                    <small class="text-center ws-nowrap text-muted">{pos}in</small>
                    <div class="d-flex justify-content-center">
                    <input type="range" id="motor-speed" class="form-range vertical" min={$system.system.calibration.bottom || 0} max={$system.system.calibration.top || 20} step={.001} bind:value={pos} oninput={() => {
                        writingPos = true;
                        if (posTimeout) clearTimeout(posTimeout);
                        posTimeout = setTimeout(commitPos, 20);
                    }} onchange={() => {
                        writingPos = false;
                    }} 
                        style="
                            width: 16px;
                            height: 400px;
                        "
                    >
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<Modal 
bind:this={modal}
    title="Edit Preset"
>
    {#snippet body()}
        {#if currentPreset}
            <div class="form-group">
                <label for="preset-name">Name</label>
                <input type="text" class="form-control" id="preset-name" bind:value={currentPreset.name} />
            </div>
            <div class="form-group">
                <label for="preset-height">Height</label>
                <input type="number" class="form-control" id="preset-height" bind:value={currentPreset.state.height} />
            </div>
        {:else}
            No Preset Selected
        {/if}
    {/snippet}
    {#snippet buttons()}
        <button type="button" class="btn btn-secondary" onclick={() => {
            modal.hide();
        }}>
            Close
        </button>
        {#if currentPreset}
            <button type="button" class="btn btn-danger" onclick={async () => {
                if (!currentPreset) return;
                if (!await confirm(`Delete ${currentPreset.name}?`)) return;
                show.removePreset(currentPreset.id);
                modal.hide();
            }}>
                Delete
            </button>
        {/if}
        <button type="button" class="btn btn-primary" onclick={() => {
            if (!currentPreset) return;
            show.update((s) => {
                const preset = s.presets.find(p => p.id === currentPreset?.id);
                if (!preset) return s;
                preset.name = currentPreset?.name || preset.name;
                preset.state.height = currentPreset?.state.height || preset.state.height;
                return s;
            });
            show.save();
            modal.hide();
        }}>
            Save
        </button>
    {/snippet}
</Modal>