<script>
    import { system } from '$lib/stores/system'; // Adjust the import path
	import { fromSnakeCase } from '$lib/text';
	import MotorState from './MotorState.svelte';
	import OsChart from './OS_Chart.svelte';

    const os_info = $derived($system.os_info);
    const tcp_connected = $derived($system.connected);
</script>

<style>
    pre, h1, h2, h3, h4, h5, h6, p, tr, td {
        font-family: 'Roboto Mono', monospace;
        margin: 0px;
    }
    
</style>
<div class="card glow p-0">
    <div class="card-header text-center stretched">
        <h5 class="card-title dashboard-title">
            System Monitor
        </h5>
    </div>
    <div class="card-body p-1 os-monitor">
        <div class="container-fluid p-0">
            <div class="row mb-1">
                <div class="col-4 ">
                    <div class="card ">
                        <div class="card-body p-1 ">
                            <pre class="p-0 m-0 no-scroll-x bg-black text-primary ">
  Network Info
  {os_info.ip_address}
  tcp port {os_info.tcp} {tcp_connected ? '✔️' : '❌'}
  osc port {os_info.osc}
  udp port {os_info.udp}
                            </pre>
                        </div>
                    </div>
                </div>
                <div class="col-3 ">
                    <div class="container-fluid p-0 ">
                        <div class="row p-0">
                            <div class="col-12 p-0 ">
                                <div class="card ">
                                    <div class="card-body p-1 no-scroll-x ">
                                        <h6 class="text-center ws-nowrap">Status</h6>
                                        {#if $system.connected}
                                            <p class="text-success text-center no-scroll-x ws-nowrap">connected</p>
                                        {:else}
                                            <p class="text-danger text-center no-scroll-x ws-nowrap">not connected</p>
                                        {/if}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="row p-0">
                            <div class="col-12 p-0 ">
                                <div class="card ">
                                    <div class="card-body p-1 no-scroll-x ">
                                        <h6 class="text-center no-scroll-x ws-nowrap">State</h6>
                                        {#if $system.connected}
                                        <!-- {#if $system.system.state === 'FAIL'}
                                        {/if} -->
                                            {#if $system.system.global_state == 'RUNNING' }
                                                <p class="text-primary text-center no-scroll-x ws-nowrap">{fromSnakeCase($system.system.state.toLowerCase())}</p>
                                            {:else}
                                                <p class="text-warning text-center no-scroll-x ws-nowrap">{$system.system.global_state.toLowerCase()}</p>
                                            {/if}
                                        {:else}
                                            <p class="text-danger text-center no-scroll-x ws-nowrap">unknown</p>
                                        {/if}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="row p-0">
                            <div class="col-12 p-0 ">
                                <div class="card ">
                                    <div class="card-body p-1 no-scroll-x ">
                                        <h6 class="text-center no-scroll-x ws-nowrap">Ready</h6>
                                        {#if $system.connected}
                                            {#if $system.system.command_ready}
                                                <p class="text-primary text-center no-scroll-x ws-nowrap">true</p>
                                            {:else}
                                                <p class="text-danger text-center no-scroll-x ws-nowrap">false</p>
                                            {/if}
                                        {:else}
                                            <p class="text-danger text-center no-scroll-x ws-nowrap">false</p>
                                        {/if}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-5">
                    <div class="card">
                        <div class="card-body p-1">
                            <OsChart />
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <MotorState />
            </div>
        </div>
    </div>
</div>