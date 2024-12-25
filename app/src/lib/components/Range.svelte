<script lang="ts">
    interface Props {
        value: number;
        min: number;
        max: number;
        step: number;
        disabled: boolean;
    }

    const { value, min = 0, max = 100, step = 1, disabled }: Props = $props();
</script>

<input type="range" {value} {min} {max} {step} {disabled} class="form-range" />

