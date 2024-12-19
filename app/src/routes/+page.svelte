<script lang="ts">
    type Preset = {
        name: string;
        height: number;
    };
    type State = {
        height: number;
        presets: Preset[];
        currentPreset?: Preset;

        presetName: string;
    };

    const state = $state<State>({
        height: 0,
        presets: [
            { name: 'Taylor', height: 100 },
            { name: 'Jake', height: 200 },
            { name: 'Conner', height: 300 },
        ],
        presetName: '',
    });

    const increment = (num: number) => {
        state.height += num;
        state.currentPreset = undefined;
    };
</script>

<h1>Current height: {state.height}</h1>
<div role="group" class="btn-group">
    <button type="button" class="btn btn-success" onclick={() => increment(1)}>Up</button>
    <button type="button" class="btn btn-danger" onclick={() => increment(-1)}>Down</button>
</div>

{#each state.presets as preset}
    <button type="button" class="btn btn-secondary" onclick={() => {
        state.height = preset.height;
        state.currentPreset = preset;
    }}>{preset.name}</button>
{/each}

{#if state.currentPreset && state.height === state.currentPreset.height}
    <p class="alert alert-success">You are at the preset height of {state.currentPreset.name}</p>
{/if}

<!-- {#if !state.currentPreset} -->
    <input type="text" class="form-control" bind:value={state.presetName} placeholder="Enter a name" />
    <button type="button" class="btn btn-primary" onclick={() => {
        if (!state.presetName) return;
        state.presets.push({ name: state.presetName, height: state.height });
        state.presetName = '';
    }}>Add Preset</button>
<!-- {/if} -->