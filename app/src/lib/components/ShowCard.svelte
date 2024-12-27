<script lang="ts">
	import type { Show } from "$lib/stores/show.svelte";
    import { goto } from "$app/navigation";
    import { prompt, confirm, colorPicker } from "$lib/prompts.svelte";

    interface Props {
        show: Show;
    }

    const { show }: Props = $props();

    const edit = async (show: Show) => {
        const name = await prompt('Enter Show Name', {
            default: show.name,
        }) || show.name;
        const color = await colorPicker('Enter Show Color', {
            default: show.color,
        }) || show.color;
        show.update(s => {
            s.name = name;
            s.color = color;
            return s;
        });

        show.save();
    };
    const remove = async (show: Show) => {
        if (await confirm(`Are you sure you want to delete ${show.name}? This will delete all its presets.`, {
            title: 'Delete Show',
        })) {
            show.delete();
        }
    };
    const open = (show: Show) => {
        goto(`/show/${show.id}`);
    }
</script>

<div style="--glow-color: {$show.color}">
    <div class="card p-0 glow">
        <div class="card-header d-flex justify-content-between">
            <h5>{$show.name}</h5>
            <div class="d-flex">
                <button type="button" class="btn btn-sm btn-primary" onclick={() => open(show)}>Open</button>
                <button type="button" class="btn btn-sm btn-primary" onclick="{() => edit(show)}">Edit</button>
                <button type="button" class="btn btn-sm btn-danger" onclick="{() => remove(show)}">Delete</button>
            </div>
        </div>
        <div class="card-body">
            <p>
                Presets: {$show.presets.length}
            </p>
        </div>
    </div>
</div>
