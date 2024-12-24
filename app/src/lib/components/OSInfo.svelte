<script lang="ts">
    import { system } from "$lib/stores/system";
    import { Chart } from 'chart.js';

    type Data = {
        cpu_usage: number;
        cpu_temp: number;
        ram: number;
        timestamp: Date;
    };

    const data: Data[] = [];

    let canvas: HTMLCanvasElement;
    let chart: Chart;
    $effect(() => {
        const last = data[data.length - 1];
        if ($system.os_info.updated == 0) return;
        if (last && last.timestamp.getTime() == $system.os_info.updated) return;

        const newData: Data = {
            cpu_usage: $system.os_info.cpu_usage,
            cpu_temp: $system.os_info.cpu_temp,
            ram: $system.os_info.ram,
            timestamp: new Date($system.os_info.updated),
        };
        data.push(newData);
        if (data.length > 10) {
            data.shift();
        }

        const labels = data.map(d => d.timestamp.toLocaleTimeString());
        const datasets = [
            {
                label: 'CPU Usage',
                data: data.map(d => d.cpu_usage),
            },
            {
                label: 'CPU Temp',
                data: data.map(d => d.cpu_temp),
            },
            {
                label: 'RAM',
                data: data.map(d => d.ram),
            }
        ];

        if (chart) {
            chart.data.labels = labels;
            chart.data.datasets = datasets;
            chart.update()
        } else {
            const ctx = canvas.getContext('2d');
            if (!ctx) return;
            chart = new Chart(ctx, {
                data: {
                    datasets,
                    labels,
                },
                type: 'line',
                options: {
                    animation: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                        }  
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: (ti) => {
                                    if (ti.dataset.label == 'CPU Usage') {
                                        return `${ti.dataset.label}: ${ti.formattedValue}%`;
                                    } else if (ti.dataset.label == 'CPU Temp') {
                                        return `${ti.dataset.label}: ${ti.formattedValue}°C`;
                                    } else {
                                        return `${ti.dataset.label}: ${ti.formattedValue}%`;
                                    }
                                }
                            }
                        }
                    }
                }
            });
        }
    });
</script>

<canvas bind:this={canvas}></canvas>