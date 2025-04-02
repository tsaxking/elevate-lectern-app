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
        self.style.setProperty('--glow-color', color.toString('rgb'), 'important');
    });
</script>


<div bind:this={self}>
    <ShowBanner {show} />
    <div class="container-fluid p-3 height py-0 w-100 no-scroll-x">
        <div class="row h-100">
            <div class="col-lg-7 col-md-12">
                <div class="container-fluid m-0 p-0">
                    <div class="row mb-2">
                        <SystemMonitor />
                    </div>
                    <div class="row mb-2">
                        <div class="col-6 m-0 p-1">
                            <Sensors />
                        </div>
                        <div class="col-6 m-0 p-1">
                            <CommandMonitor {show} />
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-5 col-md-12 h-100 px-1">
                <SystemControl bind:show={show} />
            </div>
        </div>
    </div>
</div>

<style>
    /* .height {
        height: calc(100vh - 20px);
    } */
</style>