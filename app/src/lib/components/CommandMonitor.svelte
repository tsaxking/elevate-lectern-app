<script lang="ts">
    import { system } from "$lib/stores/system";
    import { send } from "$lib/osc";
    import type { Command } from "$lib/types";
	import { confirm, select, prompt, choose } from "$lib/prompts.svelte";
	import type { Show } from "$lib/stores/show.svelte";

    interface Props {
        show: Show;
    }

    const { show }: Props = $props();

    const latest_command = $derived($system.system.current_command);

    const run = async (command: Command) => {
        if (await confirm(`Run ${command.command} with args ${command.args.join(', ')}?`)) {
            send(command.command.replace('/', '') as any, command.args[0]);
        }
    };

    type CommandList = {
        command: '/move' | '/stop' | '/go_to' | '/bump' | '/preset' | '/shutdown';
        argType: 'number' | 'text' | '';
        argName: string;
        converter?: (arg: string) => any;
    }[];



    const custom = async () => {
        // Built in here so we can use the system calibration as a $state
        const commandList: CommandList = [
        {
            command: '/move',
            argType: 'number',
            argName: 'speed (-1 to 1)',
            converter: (arg) => parseFloat(arg),
        },
        {
            command: '/stop',
            argType: '',
            argName: '',
        },
        {
            command: '/go_to',
            argType: 'number',
            argName: `position (${$system.system.calibration.bottom} to ${$system.system.calibration.top})`,
            converter: (arg) => parseFloat(arg),
        },
        {
            command: '/bump',
            argType: 'number',
            argName: 'speed (-1 to 1)',
            converter: (arg) => parseFloat(arg),
        },
        {
            command: '/preset',
            argType: 'text',
            argName: 'preset',
        },
        {
            command: '/shutdown',
            argType: '',
            argName: '',
        }
    ];
        const command = await select('Select Command', commandList.map(c => c.command));
        if (!command) return;
        if (command === '/stop') return run({ command, args: [] });
        if (command === '/preset') {
            const preset = await select('Select Preset', $show.presets, {
                render: (p) => p.name,
            });
            if (!preset) return;
            run({
                command,
                args: [`${show.id}.${preset.id}`],
            });
            return; // TODO: Implement presets
        }
        const c = commandList.find(c => c.command === command);
        if (!c) return;
        if (!c.argType) return run({ command, args: [] });
        
        const args = await prompt(`Enter ${command} Args (${c.argName})`, {
                type: c.argType,
            }) || '';
        if (!args) return;

        PRESET: if (command === '/go_to') {
            if (await confirm('Do you want to turn this command into a preset?', {
                title: "Create Preset"
            })) {
                const name = await prompt('Enter Preset Name');
                if (!name) break PRESET;
                show.addPreset({
                    name,
                    state: {
                        height: parseFloat(args),
                    },
                    id: show.nextPresetId(),
                });
                // We're still going to run the /go_to command because we don't know if the preset will be saved by the time the python script tries to open it
            }
        }

        run({
            command,
            args: [c.converter ? c.converter(args) : args],
        });
    };
</script>

<div class="card p-0 glow m-0">
    <div class="card-header">
        <h5 class="card-title text-center">Command Monitor</h5>
    </div>
    <div class="card-body p" style="height: 361px; overflow-y: scroll;">
        <div class="container-fluid">
            <div class="row mb-1">
                <button type="button" class="btn btn-secondary w-100 h-100" onclick={custom}>
                    Run Custom
                </button>
            </div>
            <div class="row mb-1">
                <p>Most Recent Command: (click to run again)</p>
                {#if latest_command}
                    <button type="button" class="btn btn-primary w-100" onclick={() => run(latest_command)}>
                        {latest_command.command}: {latest_command.args.join(', ')}
                    </button>
                {/if}
            </div>
            <div class="row">
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