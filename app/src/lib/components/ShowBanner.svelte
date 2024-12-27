<script lang="ts">
	import { Color } from "$lib/colors/color";
	import { colorPicker, prompt } from "$lib/prompts.svelte";
	import type { Show } from "$lib/stores/show.svelte";

    interface Props {
        show: Show;
    }

    let self: HTMLDivElement;


    const { show }: Props = $props();

    const changeName = async (e: Event) => {
        e.preventDefault();
        const name = await prompt('Enter a new name for the show', {
            default: show.name
        });
        if (name) {
            show.update(s => {
                s.name = name;
                return s;
            });
        }

        show.save();
    };

    const changeColor = async (e: Event) => {
        e.preventDefault();
        if (!Object.is(self, e.target)) {
            return;
        }
        const color = await colorPicker('Enter a new color for the show', {
            default: show.color
        });
        if (color) {
            show.update(s => {
                s.color = color;
                return s;
            });
        }

        show.save();
    };

    let textColor = $state('black');

    $effect(() => {
        const c = new Color($show.color);
        const w = c.detectContrast(Color.fromName('white'));
        const b = c.detectContrast(Color.fromName('black'));

        textColor = w > b ? 'white' : 'black';

        console.log('textColor', textColor);
    });
</script>


<div class="card p-0 mb-1 w-100">
    <div bind:this={self} class="card-body d-flex justify-content-center p-1" oncontextmenu="{changeColor}" style="background-color: {$show.color};">
        <h5 oncontextmenu="{changeName}" style="color: {textColor} !important;">{$show.name}</h5>
    </div>
</div>