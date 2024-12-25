<script lang="ts">
    import { system } from "$lib/stores/system";
    import { Canvas } from "$lib/canvas/canvas";
	import { onMount } from "svelte";
    import { MotorGradient } from "./motor-gradient";

    let canvasEl: HTMLCanvasElement;

    const drawable = new MotorGradient($system, 100);

    let canvas: Canvas;

    onMount(() => {
        const ctx = canvasEl.getContext("2d");
        if (!ctx) return;
        canvas = new Canvas(ctx);
        canvas.add(drawable);
        let start = 0;
        let direction = 1;
        const stop = canvas.animate(() => {
            // drawable.filter((_, i) => i < start);
            // start += direction;
            // if (start === 0 || start === 200) direction *= -1;
        });
        return () => stop();
    });

    $effect(() => {
        drawable.setState($system);
    });
</script>

<div class="canvas-container">
    <canvas bind:this={canvasEl} width="2000" height="75" class="rounded-1"></canvas>
</div>

<style>
    .canvas-container {
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    canvas {
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
    }
</style>