<script lang="ts">
    import { onMount, onDestroy } from 'svelte';

    interface Props {
        color: string;
        rate?: number;
        flashing?: boolean;
        size?: number;
        brightness?: number;
    }

    const { color, rate = 500, flashing = false, size = 10, brightness = 1 }: Props = $props();
  
    // let flashing = $state(true); // State to control whether the LED is flashing
    // let color = $state('red'); // Default color of the LED
    // let rate = $state(500); // Flashing rate in milliseconds (default is 500ms)
    let isOn = $state(true); // LED state (on/off)
  
    // Automatically start flashing the LED
    let interval: NodeJS.Timeout;
    onMount(() => {
        return () => {
            if (interval) {
                clearInterval(interval);
            }
        }
    });
  
  
    // Update the flashing rate dynamically
    $effect(() => {
        if (!flashing && interval) {
            clearInterval(interval);
        }

        if (flashing) {
        interval = setInterval(() => {
          isOn = !isOn; // Toggle LED state
        }, rate); // Flash rate
      }
    });
  </script>
  
  <style>
    .led {
      width: 100px;
      height: 100px;
      border-radius: 50%;
      /* transition: background-color 0.1s; */
      background-color: transparent;
    }
    .led.on {
      background-color: var(--led-color);
    }
    .led.off {
      background-color: transparent;
    }
  </style>
  
<div class="led {isOn ? 'on' : 'off'}" style="--led-color: {color}; width: {size}px; height: {size}px; opacity: {Math.min(1, Math.max(0, brightness))};"></div>