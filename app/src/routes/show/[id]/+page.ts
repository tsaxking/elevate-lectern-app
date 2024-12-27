import { Show } from '$lib/stores/show.svelte.js';

export const load = async (page) => {
    const show = (await Show.open(+page.params.id)).unwrap();
    return {
        show,
    }
};