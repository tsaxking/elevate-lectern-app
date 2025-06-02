import osc from 'osc';
import { getIp } from './utils';
import type { OscCommand, TCPCommand } from '$lib/events';
import net from 'net';
import { SimpleEventEmitter } from '$lib/event-emitter';

const oscPort = new osc.UDPPort({
    // localAddress: 'localhost',
    // localPort: 12321,
    remoteAddress: '127.0.0.1',
    remotePort: 12321
});

oscPort.open();

oscPort.on('ready', () => {
    console.log('OSC ready');
});

const tcp = new net.Socket();

export const Connection = {
    connected: false,
}

let interval: NodeJS.Timeout;

const connect = () => {
    if (Connection.connected) return;
    tcp.connect(11111, 'localhost');
};

tcp.on('connect', () => {
    Connection.connected = true;
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
    if (!Connection.connected) return;
    Connection.connected = false;
    console.log('TCP disconnected');

    if (interval) clearInterval(interval);
    interval = setInterval(() => {
        connect();
    }, 5000);
};

connect();

export const sendOSC = <K extends OscCommand>(command: K) => {
    oscPort.send({ address: command, args: [0] });
}

export const sendTCP = <K extends TCPCommand>(command: K) => {
    if (!Connection.connected) connect();
    tcp.write(command);
}

const onExit = () => {
    oscPort.close();
    // tcp.end();
};