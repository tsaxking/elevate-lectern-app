import sse from './sse';
import dgram from 'dgram';
import { getIp } from './utils';
import sys from 'systeminformation';
import { $Math } from '$lib/math';

const socket = dgram.createSocket('udp4');

const os_info = {
    cpu_usage: 0,
    cpu_temp: 0,
    ip_address: 'localhost',
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

    os_info.cpu_usage = $Math.roundTo( load.currentLoad, 2);
    os_info.ram = $Math.roundTo( (ram.free / ram.total) * 100, 2);
    os_info.cpu_temp = $Math.roundTo( temp.main, 2);
    os_info.updated = Date.now();
}, 1000 * 10);

let system: unknown,
    lastMessage = 0,
    calibration: unknown;

socket.on('message', (msg, rinfo) => {
    // if (rinfo.address !== 'localhost') return; // Only allow local connections
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