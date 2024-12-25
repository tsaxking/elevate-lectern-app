export type ShowConfig = {  
    id: number;
    name: string;
    color: string;
    presets: PresetConfig[];
}

export type PresetConfig = {
    id: number;
    name: string;
    state: State;
}

export type State = {
    height: number;
}

type States = 'STAND_BY' | 'MOVING' | 'ACCELERATING' | 'LOCK' | 'UNKNOWN';

type MotorState = 'STAND_BY' | 'RUNNING' | 'STOPPING' | 'STOPPED' | 'CALIBRATING' | 'TESTING' | 'UNKNOWN';

export type Command = {
    command: string;
    args: (string|number)[];
}

export type SystemState = {
    system: {    
        sensors: {
            position: number;
            min_limit: boolean;
            max_limit: boolean;
            power: boolean;
            main_up: boolean;
            main_down: boolean;
            secondary_up: boolean;
            secondary_down: boolean;
            main_speed: number;
            secondary_speed: number;
        };
        // Non-sensors
        motor_speed: number;
        state: States;
        command_ready: boolean;
        target_speed: number;
        gpio_moving: boolean;
        gpio_target_motor_speed: number;
        target_pos: number;
        start_pos: number;
        velocity: number;
        motor_state: MotorState;
        global_state: 'SHUTDOWN' | 'STARTUP' | 'CALIBRATING' | 'RUNNING' | 'UNKNOWN';
        proximity_up: number;
        proximity_down: number;
        calibration: Calibration;
        speed_multiplier: number;
        backlog: Command[],
        current_command: Command | undefined;
    };
    os_info: {
        ip_address: string;
        cpu_usage: number;
        cpu_temp: number;
        updated: number;
        ram: number;
        osc: number;
        tcp: number;
        udp: number;
    };
    connected: boolean;
};

export type Calibration = {
    top: number;
    bottom: number;
    velocity: number;
}

export enum BootstrapColor {
    PRIMARY = 'primary',
    SECONDARY = 'secondary',
    SUCCESS = 'success',
    DANGER = 'danger',
    WARNING = 'warning',
    INFO = 'info',
    LIGHT = 'light',
    DARK = 'dark',
    WHITE = 'white',
    TRANSPARENT = 'transparent'
}