<script lang="ts">
    import { system } from "$lib/stores/system";
</script>

{#if $system.connected}
<h3 class="badge text-bg-success p-2 m-0 rounded-0">CONNECTED</h3>
{:else}
<h3 class="badge text-bg-danger p-2 m-0 rounded-0">DISCONNECTED</h3>
{/if}