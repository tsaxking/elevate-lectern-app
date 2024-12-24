import osc from 'osc';
import { getIp } from './utils';
import type { OscCommands } from '$lib/events';
import net from 'net';
import { SimpleEventEmitter } from '$lib/event-emitter';

const udpPort = new osc.UDPPort({
    localAddress: '127.0.0.1',
    localPort: 12321,
    remoteAddress: 'taylorpi.local',
    remotePort: 12321
});

udpPort.open();

udpPort.on('ready', () => {
    console.log('OSC ready');
});

// const em = new SimpleEventEmitter<'stop'>();

const tcp = new net.Socket();

let connected = false;

let interval: NodeJS.Timeout;

const connect = () => {
    if (connected) return;
    tcp.connect(11111, 'taylorpi.local');
};

tcp.on('connect', () => {
    connected = true;
    console.log('TCP connected');
    clearInterval(interval);
});

tcp.on('close', () => {
    disconnect();
});

tcp.on('error', (err) => {
    console.error(err);
    disconnect();
});

const disconnect = () => {
    if (!connected) return;
    connected = false;
    console.log('TCP disconnected');

    if (interval) clearInterval(interval);
    interval = setInterval(() => {
        connect();
    }, 5000);
};

connect();

export const send = <K extends keyof OscCommands>(command: K, data: OscCommands[K]) => {
    if (command === 'stop') return stop();
    udpPort.send({ address: `/${command}`, args: data as any });
}

const stop = () => {
    tcp.write('stop');
}

const onExit = () => {
    udpPort.close();
    tcp.end();
};