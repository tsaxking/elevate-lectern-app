<script lang="ts">
	import { system } from '$lib/stores/system.js';

    const { data } = $props();
    const show = data.show;

    const createNew = () => {
        const name = prompt('Enter Preset Name');
        if (!name) return;
        show.addPreset({
            name,
            state: {
                height: system.state.system.sensors.position
            },
            id: show.nextPresetId(),
        });
    };
</script>


<div class="container">
    <div class="row">
        <h1 class="text-center">Current Show: {show.name}</h1>
    </div>
    <div class="row">
        <button type="button" class="btn btn-primary" onclick={createNew}>
            New Preset
        </button>
    </div>
    {#each $show.presets as preset}
        <div class="row mb-3">
            <div class="card bg-secondary p-0">
                <div class="card-header">
                    <h5>{preset.name}</h5>
                </div>
                <div class="card-body">
                    <p>
                        {preset.state.height}
                    </p>
                </div>
            </div>
        </div>
    {/each}
</div>