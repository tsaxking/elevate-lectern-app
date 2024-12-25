<script lang="ts">
    import SystemMonitor from "$lib/components/SystemMonitor.svelte";
	import SystemControl from '$lib/components/SystemControl.svelte';
	import Sensors from '$lib/components/Sensors.svelte';
    import CommandMonitor from '$lib/components/CommandMonitor.svelte';
	import ShowBanner from "$lib/components/ShowBanner.svelte";
	import { onMount } from "svelte";
	import { Color } from "$lib/colors/color.js";

    const { data } = $props();
    let show = $state(data.show);

    let self: HTMLDivElement;


    $effect(() => {
        const color = Color.fromHex($show.color);
        // self.style.setProperty('--bs-border-color', color.toString('hex'), 'important');
        // self.style.setProperty('--bs-card-border-color', color.toString('hex'), 'important');
        // self.style.setProperty('--bs-body-color-rgb', color.toString('hex'), 'important');

    });
</script>


<div bind:this={self}>
    <ShowBanner {show} />
    <div class="container-fluid p-3 py-0 vh-100 w-100">
        <div class="row h-100">
            <div class="col-8">
                <div class="container-fluid m-0 p-0">
                    <div class="row mb-2">
                        <SystemMonitor />
                    </div>
                    <div class="row mb-2">
                        <Sensors />
                    </div>
                    <div class="row">
                        <CommandMonitor />
                    </div>
                </div>
            </div>
            <div class="col-4 h-100 px-1">
                <SystemControl bind:show={show} />
            </div>
        </div>
    </div>
</div>