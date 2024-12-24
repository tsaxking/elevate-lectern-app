<script lang="ts">
    import { system } from "$lib/stores/system";
	import { BootstrapColor as BS } from "$lib/types";
    let color: BS = $state(BS.WHITE);

    $effect(() => {
        switch ($system.system.state) {
            case 'LOCK':
            case 'UNKNOWN':
                color = BS.DANGER;
                break;
            // case 'STARTUP':
            // case 'SHUTDOWN':
            // case 'CALIBRATING':
            //     color = BS.WARNING;
            //     break;
            case 'STAND_BY':
            case 'ACCELERATING':
            case 'MOVING':
                color = BS.PRIMARY;
                break;
        }
    });
</script>

{#snippet Connected()}
    {#if $system.connected}
        <span class="position-absolute top-0 start-100 translate-middle p-1 bg-success border rounded-circle">
            <span class="visually-hidden">New alerts</span>
        </span>
    {:else}
        <span class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border rounded-circle">
            <span class="visually-hidden">New alerts</span>
        </span>
    {/if}
{/snippet}

{#if $system.connected}
    <h3 class="badge text-bg-{color} p-2 m-0 rounded-0 position-relative">{$system.system.state}{@render Connected()}</h3>
{:else}
    <h3 class="badge text-bg-secondary p-2 m-0 rounded-0 position-relative">UNKNOWN{@render Connected()}</h3>
{/if}