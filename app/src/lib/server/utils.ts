import { attempt, attemptAsync } from '../check';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

const DIR = path.resolve(process.cwd(), '../json');

const mkDir = async () => {
    return attemptAsync(async () => {
        await fs.mkdir(
            DIR,
            { recursive: true }
        )
    });
}

export const getJSON = async <T = unknown>(name: string) => {
    return attemptAsync<T>(async () => {
        const file = path.resolve(DIR, `${name}.json`);
        const data = await fs.readFile(file, 'utf-8');
        return JSON.parse(data) as T;
    });
}


export const saveJSON = async <T>(name: string, data: T) => {
    return attemptAsync(async () => {
        const file = path.resolve(DIR, `${name}.json`);
        await mkDir(); // Don't unwrap because we don't care if it fails
        await fs.writeFile(file, JSON.stringify(data, null, 2));
    });
}

export const getJSONS = async () => {
    return attemptAsync(async () => {
        return fs.readdir(DIR);
    });
}

export const deleteJSON = async (name: string) => {
    return attemptAsync(async () => {
        const file = path.resolve(DIR, `${name}.json`);
        await fs.unlink(file);
    });
}

export const getIp = () => {
    return  attempt(() => {
        const interfaces = os.networkInterfaces();
        const eth0 = interfaces.eth0 || interfaces.en0;

        if (!eth0) return 'localhost';

        const ipv4 = eth0.find(i => i.family === 'IPv4');

        if (!ipv4) return 'localhost';

        return ipv4.address;
    });
}