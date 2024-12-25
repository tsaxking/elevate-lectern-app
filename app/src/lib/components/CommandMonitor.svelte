<script lang="ts">
    import { system } from "$lib/stores/system";
    import { send } from "$lib/osc";
    import type { Command } from "$lib/types";

    const latest_command = $derived($system.system.current_command);

    const run = (command: Command) => {
        send(command.command.replace('/', '') as any, command.args[0]);
    };
</script>

<div class="card p-0 shadow">
    <div class="card-header">
        <h5 class="card-title">Command Monitor</h5>
    </div>
    <div class="card-body p">
        <div class="container-fluid">
            <div class="row">
                <div class="col-8">
                    <p>Most Recent Command: (click to run again)</p>
                    {#if latest_command}
                        <button type="button" class="btn btn-primary w-100" onclick={() => run(latest_command)}>
                            {latest_command.command}: {latest_command.args.join(', ')}
                        </button>
                    {/if}
                </div>
                <div class="col-4">
                    <p>Command Backlog:</p>
                    <ul class="list-group">
                        {#each $system.system.backlog as c}
                            <li class="list-group-item">
                                {c.command}: {c.args.join(', ')}
                            </li>
                        {/each}
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>