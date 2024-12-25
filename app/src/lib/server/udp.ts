import sse from './sse';
import dgram from 'dgram';
import { getIp } from './utils';
import sys from 'systeminformation';
import { $Math } from '$lib/math';
import { nowSmall } from '$lib/clock';

const socket = dgram.createSocket('udp4');

const os_info = {
    cpu_usage: 0,
    cpu_temp: 0,
    ip_address: 'taylorpi.local',
    ram: 0,
    updated: Date.now(),
    osc: 12321,
    tcp: 11111,
    udp: 41234,
};


setInterval(async () => {
    os_info.ip_address = getIp().unwrap();
    const [
        load,
        ram,
        temp,
    ] = await Promise.all([
        sys.currentLoad(),
        sys.mem(),
        sys.cpuTemperature(),
    ]);

    os_info.cpu_usage = $Math.roundTo(2, load.currentLoad);
    os_info.ram = $Math.roundTo(2, (ram.free / ram.total) * 100);
    os_info.cpu_temp = $Math.roundTo(2, temp.main);
    os_info.updated = Date.now();
}, 1000 * 10);

let system: unknown,
    lastMessage = 0,
    calibration: unknown;

socket.on('message', (msg, rinfo) => {
    // if (rinfo.address !== '127.0.0.1') return; // Only allow local connections
    try {
        const data = JSON.parse(msg.toString());
        // if (data.i_am === 'calibration') {
        //     calibration = data;
        // } else {
            system = data;
        // }
        lastMessage = Date.now();
    } catch (error) {
        console.error(error);
    }
    // console.log('system', system);
    // console.log('os_info', os_info);
    // console.log(`server got: ${JSON.stringify(data, null, 4)}`);
});

socket.on('error', (err) => {
    console.error(`Server error:\n${err.stack}`);
    // server.close();
});

setInterval(() => {
    sse.send('state', {
        system,
        os_info
    });

    if (lastMessage < Date.now() - 1000) {
        system = undefined;
    }
}, 10);

// setInterval(() => {
//     if (calibration) {
//         sse.send('calibration', calibration);
//     }
// }, 1000);
  

socket.bind(41234);

process.on('exit', () => {
    socket.close();
});