<script lang="ts">
	import { goto } from "$app/navigation";
	import ShowCard from "$lib/components/ShowCard.svelte";
	import { colorPicker, confirm, prompt } from "$lib/prompts.svelte";
    import { Show } from "$lib/stores/show.svelte";

    const shows = Show.getAll(true);

    const createNew = async () => {
        const name = await prompt('Enter Show Name');
        if (!name) return;
        Show.new({
            name,
            presets: [],
            color: '#000000',
        });
    };
</script>


<div class="container mt-3">
    <div class="row mb-3">
        <button type="button" class="btn btn-primary glow" onclick={createNew}>New Show</button>
    </div>
    {#each shows as show}
        <div class="row mb-3">
            <ShowCard show={show} />
        </div>
    {/each}
</div>