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
        }
    ]);

    let motorSpeed = $state(0);
    const commit = () => {
        // const num = M.roundTo(3, motorSpeed);
        send('move', motorSpeed.toFixed(3));
    };

    let timeout: NodeJS.Timeout;

    let modal: Modal;
    let currentPreset: PresetConfig | null = $state(null);
</script>

<div class="card p-0 glow h-100">
    <div class="card-header">
        <h5 class="card-title dashboard-title">System Control</h5>
    </div>
    <div class="card-body p-0 system-controller h-100">
        <div class="container-fluid p-0">
            <div class="row">
                <div class="col px-3 mb-0">
                    <h6 class="text-center">Motor Speed:</h6>
                    <input id="motor-speed" type="range" class="form-range" min="{-1}" max="{1}" step="{0.001}" bind:value={motorSpeed} oninput={() => {
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
            <div class="row">
                {#each buttons as button}
                    <div class="col-12">
                        <button type="button" class="btn w-100 my-2 btn-sm btn-{button.color}" onclick={button.action} disabled={button.disabled} oncontextmenu="{button.contextmenu}">
                            {button.name}
                        </button>
                    </div>
                {/each}
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