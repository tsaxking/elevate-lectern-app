<script lang="ts">
    interface Props {
        value: number;
        min: number;
        max: number;
        step: number;
        disabled: boolean;
        style?: string;
        vertical?: boolean;
    }

    const { value, min = 0, max = 100, step = 1, disabled, style = '', vertical = false }: Props = $props();
</script>

<input type="range" {value} {min} {max} {step} {disabled} class="form-range" class:vertical={vertical} style={style} />