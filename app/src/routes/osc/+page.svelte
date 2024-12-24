<script lang="ts">
    import { send } from "$lib/osc";


    const move = () => {
        const speed = prompt('Enter Speed');
        if (Number.isNaN(speed)) return;

        send('move', Number(speed));
    };

    const stop = () => {
        send('stop', undefined);
    };
</script>


<h1>OSC</h1>

<button type="button" class="btn btn-primary" onclick={move}>Move</button>

<button type="button" class="btn btn-danger" onclick={stop}>Stop</button>