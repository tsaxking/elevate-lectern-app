<script lang="ts">
    import { Show } from "$lib/stores/show.svelte";
    import { system } from "$lib/stores/system";
	import { BootstrapColor, type PresetConfig } from "$lib/types.js";
    import { All as OSC } from "$lib/osc.js";
    import { All as TCP } from '$lib/tcp.js';
    import Modal from "./Modal.svelte";
    import { goto } from "$app/navigation";
	import { alert, confirm, prompt, select } from "$lib/prompts.svelte";
	import { $Math as M } from "$lib/math";
    import { onMount } from "svelte";
    import { contextmenu } from '$lib/contextmenu.js';


    interface Props {
        show: Show;
    }

    const { show = $bindable() }: Props = $props();

    let current: PresetConfig | undefined = $state(undefined);
    let offset: number = $state(0);
    let editName: string = $state('');
    let editHeight: number = $state(0);

    const prev = () => {
        if (current) {
            const i = $show.presets.findIndex(p => p.id === current?.id);
            console.log('prev', i, $show.presets);
            current = $show.presets[i - 1] || $show.presets[0];
        } else {
            current = $show.presets[$show.presets.length - 1];
        }
    };

    const next = () => {
        if (current) {
            const i = $show.presets.findIndex(p => p.id === current?.id);
            console.log('next', i, $show.presets);
            current = $show.presets[i + 1] || $show.presets[0];
        } else {
            current = $show.presets[0];
        }
    };

    const moveUp = () => {
        if (current) {
            const i = $show.presets.findIndex(p => p.id === current?.id);
            if (i > 0) {
                const temp = $show.presets[i - 1];
                $show.presets[i - 1] = current;
                $show.presets[i] = temp;
                renumber();
            }
        }
    }

    const moveDown = () => {
        if (current) {
            const i = $show.presets.findIndex(p => p.id === current?.id);
            if (i < $show.presets.length - 1) {
                const temp = $show.presets[i + 1];
                $show.presets[i + 1] = current;
                $show.presets[i] = temp;
                renumber();
            }
        }
    };

    const rightClick = (preset: PresetConfig) => {
        contextmenu();
    }

    const go = () => {
        if (!current) {
            return alert('No cue selected');
        }
        OSC.Lectern.goTo(current.state.height);
        next();
    };

    const store = async () => {
        const name = await prompt('Enter a name for the preset:');
        if (!name) {
            return;
        }
        const index = $show.presets.findIndex(p => p.id === current?.id);
        if (index === -1) {
            show.addPreset({
                id: 0,
                name,
                state: {
                    height: $system.system.sensors.position,
                }
            });
            show.save();
            current = show.presets[show.presets.length - 1];
            return;
        }

        const newPreset: PresetConfig = {
            id: index + 2,
            name: name,
            state: {
                height: $system.system.sensors.position,
            }
        };

        show.update(s => {
            const presets = [...s.presets];
            presets.splice(index + 1, 0, newPreset);
            return {
                ...s,
                presets: presets
            };
        });
        renumber();
    }

    const renumber = () => {
        show.update(s => ({
            ...s,
            presets: s.presets.map((preset, index) => ({
                ...preset,
                id: index + 1
            }))
        }))
        show.save();
    };

    const edit = (preset: PresetConfig) => {
        editName = preset.name;
        current = preset;
        editHeight = preset.state.height;
        editModal.show();
        onblur();
    }

    const instructions = () => {
        instructionsModal.show();
    };

    const remove = async () => {
        if (!current) return;
        if (await confirm(`Are you sure you want to remove the cue ${current.name}?`)) {
            if (!current) return;
            show.update(s => ({
                ...s,
                presets: s.presets.filter(p => p.id !== current?.id)
            }));
            current = undefined;
            show.save();
        }
    }

    let instructionsModal: Modal;
    let editModal: Modal;

    const onkeyListener = (event: KeyboardEvent) => {
        if (!focus) return;
        if (event.ctrlKey) {
            switch (event.key) {
                case 'ArrowLeft':
                case 'ArrowUp':
                    event.preventDefault();
                    moveUp();
                    break;
                case 'ArrowDown':
                case 'ArrowRight':
                    event.preventDefault();
                    moveDown();
                    break;
                case 'Enter':
                case ' ':
                    event.preventDefault(); 
                    if (current) {
                        edit(current);
                    }
                    break;
            }
            return;
        }
        switch (event.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                prev();
                break;
            case 'ArrowDown':
            case 'ArrowRight':
                next();
                break;
            case 'Enter':
            case ' ':
                go();
                break;
            case 'Escape':
                TCP.stop();
                break;
            case 'Delete':
            case 'Backspace':
                remove();
                break;
            case 'i':
                instructions();
                break;
        }
    }

    let focus = $state(false);

    const onfocus = () => {
        console.log('focus');
        // onkey();
        focus = true;
    }
    const onblur = () => {
        console.log('blur');
        // offkey();
        focus = false;
    }

    onMount(() => {
        instructionsModal.on('show', onblur);
        instructionsModal.on('hide', onfocus);
        document.addEventListener('keydown', onkeyListener);
        current = $show.presets[0];
        return () => {
            document.removeEventListener('keydown', onkeyListener);
        }
    });
</script>

<div class="card glow">
    <div class="card-header">
        <h5 class="card-title dashboard-title">System Control</h5>
    </div>
    <div class="card-body">
        <div class="container-fluid"
    tabindex="0"
    class:focus={focus}
    onfocus={onfocus}
    onblur={onblur}
>
    <div class="row mb-3">
        <div class="col">
            <div class="d-flex justify-content-between align-items-middle">
                <button type="button" class="btn btn-info" onclick={(e) => {
                    instructions();
                    e.currentTarget.blur();
                    onblur();
                }}>
                    Instructions
                </button>
                <button type="button" class="btn btn-primary" onclick={(e) => {
                    renumber();
                    e.currentTarget.blur();
                    onblur();
                }}>
                    Renumber
                </button>
                <button type="button" class="btn btn-secondary" onclick={(e) => {
                    store();
                    e.currentTarget.blur();
                    onblur();
                }}>
                    Store
                </button>
                <button type="button" class="btn btn-success" onclick={(e) => {
                    go();
                    e.currentTarget.blur();
                    onblur();
                }}>
                    Go
                </button>
            </div>
        </div>
    </div>
    <div class="row mb-3">
        <div class="table-responsive">
            <table class="" style="width: 100%">
                <colgroup>
                    <col span="1" style="width: 10%">
                    <col span="1" style="width: 60%">
                    <col span="1" style="width: 10%">
                    <col span="1" style="width: 10%">
                    <col span="1" style="width: 10%">
                </colgroup>
                <thead>
                    <tr>
                        <th>
                            Cue #
                        </th>
                        <th>
                            Name
                        </th>
                        <th>
                            Lectern
                        </th>
                        <th>
                            Tele 1
                        </th>
                        <th>
                            Tele 2
                        </th>
                    </tr>
                </thead>
                <tbody>
                {#each $show.presets as preset}
                    <tr
                        class="clickable"
                        class:current={current && current.id === preset.id}
                        onclick={() => current=preset}
                        ondblclick={() => {
                            onblur();
                        }}
                        oncontextmenu={(e) => {
                            e.preventDefault();
                            rightClick(preset);
                        }}
                    >
                        <td>
                            {preset.id}
                        </td>
                        <td>
                            {preset.name}
                        </td>
                        <td>
                            {preset.state.height}
                        </td>
                        <td></td>
                        <td></td>
                    </tr>
                {/each}
                </tbody>
            </table>
        </div>
    </div>
</div>

    </div>
</div>

{#snippet text(text: string)}
    <span class="text-info">{text}</span>
{/snippet}


<Modal title="Cue Table Instructions" bind:this={instructionsModal}>
    {#snippet body()}
        <ul>
            <li>
                You cannot use the keyboard unless the System Control card is focused. To focus, click on the card and it will change color.
            </li>
            <li>
                Use the arrow keys to navigate through the cues. {@render text('Left/Right')} or {@render text('Up/Down')} will move to the previous or next cue.
            </li>
            <li>
                {@render text('Space/Enter')} will trigger the selected cue.
            </li>
            <li>
                Triggering a cue will automatically select the next cue in the list.
            </li>
            <li>
                {@render text('Ctrl + Up/Down')} or {@render text('Ctrl + Left/Right')} will move the selected cue up or down in the list.
            </li>
            <li>
                {@render text('Ctrl + Space')} or {@render text('Ctrl + Enter')} will propmt you to edit the current cue.
            </li>
            <li>
                Storing a new cue will place the new cue after the current cue.
            </li>
            <li>
                {@render text('Delete/Backspace')} will remove the current cue from the list.
            </li>
            <li>
                {@render text('i')} will show this instructions modal.
            </li>
        </ul>
    {/snippet}
    {#snippet buttons()}
        <button type="button" class="btn btn-primary" onclick={() => instructionsModal.hide()}>
            Ok
        </button>
    {/snippet}
</Modal>

<Modal title="Edit Cue" bind:this={editModal}>
    {#snippet body()}
        <p>Editing cue {current?.id} - {current?.name}</p>
        <div class="form-group">
            <label for="cue-name">Cue Name</label>
            <input type="text" id="cue-name" class="form-control" bind:value={editName} />
        </div>
        <div class="form-group">
            <label for="cue-height">Lectern Height</label>
            <input type="number" id="cue-height" class="form-control" bind:value={editHeight} step="0.25" />
        </div>
    {/snippet}
    {#snippet buttons()}
        <button type="button" class="btn btn-primary" onclick={() => {
            if (current) {
                show.update(s => ({ 
                    ...s,
                    presets: s.presets.map(p => {
                        if (p.id === current?.id) {
                            p.name = editName;
                            p.state.height = editHeight;
                        }
                        return p;
                    })
                }));
                show.save();
            }
            editModal.hide();
        }}>
            Save
        </button>
        <button type="button" class="btn btn-secondary" onclick={() => editModal.hide()}>
            Cancel
        </button>
    {/snippet}
</Modal>

<style>
    .focus {
        background-color: hsla(285, 47%, 56%, 0.481);
    }
    .clickable {
        cursor: pointer;
    }

    .clickable:hover {
        color: var(--bs-secondary);
    }

    .current {
        background-color: var(--bs-primary);
        color: var(--bs-white);
    }
</style>