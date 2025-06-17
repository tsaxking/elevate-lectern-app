<script lang="ts">
    import SystemMonitor from "$lib/components/SystemMonitor.svelte";
	import SystemControl from '$lib/components/SystemControl.svelte';
	import Sensors from '$lib/components/Sensors.svelte';
    import CommandMonitor from '$lib/components/CommandMonitor.svelte';
	import ShowBanner from "$lib/components/ShowBanner.svelte";
	import { onMount } from "svelte";
    import CueTable from "$lib/components/CueTable.svelte";
	import { Color } from "$lib/colors/color.js";

    const { data } = $props();
    let show = $state(data.show);

    let self: HTMLDivElement;


    $effect(() => {
        const color = Color.fromHex($show.color);
        // self.style.setProperty('--bs-border-color', color.toString('hex'), 'important');
        // self.style.setProperty('--bs-card-border-color', color.toString('hex'), 'important');
        self.style.setProperty('--glow-color', color.toString('rgb'), 'important');
    });
</script>


<div bind:this={self}>
    <ShowBanner {show} />
    <div class="container-fluid p-3 height py-0 w-100 no-scroll-x">
        <div class="row h-100">
            <div class="col-md-5">
                <CueTable bind:show={show} />
            </div>
            <div class="col-md-3">
                <SystemControl bind:show={show} />
            </div>
            <div class="col-md-4">
                <SystemMonitor />
                <Sensors />
            </div>
        </div>
    </div>
</div>

<style>
    /* .height {
        height: calc(100vh - 20px);
    } */
</style>