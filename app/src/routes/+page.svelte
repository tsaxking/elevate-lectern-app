<script>
    import { Show } from "$lib/stores/show";

    const shows = Show.getAll();

    const createNew = () => {
        const name = prompt('Enter Show Name');
        if (!name) return;
        Show.new({
            name,
            presets: []
        });
    };
</script>

<button type="button" class="btn btn-primary" onclick={createNew}>New</button>

<div class="container">
    {#each $shows as show}
        <div class="row mb-3">
            <a href="/show/{show.id}" class="text-decoration-none">
                <div class="card bg-secondary p-0">
                    <div class="card-header">
                        <h5>{show.name}</h5>
                    </div>
                    <div class="card-body">
                        <p>
                            Presets: {show.presets.length}
                        </p>
                    </div>
                </div>
            </a>
        </div>
    {/each}
</div>