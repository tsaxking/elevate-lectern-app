declare module "osc" {
    type Address = string; // e.g., "/example/address"
    type Port = number; // UDP/TCP port number
  
    interface OSCMessage {
      address: Address;
      args?: Array<string | number | object | boolean>;
    }
  
    interface OSCBundle {
      timetag?: number | Date;
      packets: Array<OSCMessage | OSCBundle>;
    }
  
    interface OSCOptions {
      metadata?: boolean;
      unpackSingleArgs?: boolean;
      raw?: boolean;
    }
  
    interface OSCSocketOptions {
      remoteAddress?: string;
      remotePort?: Port;
      localAddress?: string;
      localPort?: Port;
      broadcast?: boolean;
      multicastMembership?: string[];
      metadata?: boolean;
      raw?: boolean;
    }
  
    interface OSCEvent {
      address: Address;
      args?: Array<string | number | object | boolean>;
    }
  
    class UDPPort {
      constructor(options: OSCSocketOptions);
  
      open(): void;
      close(): void;
      send(message: OSCMessage | OSCBundle, remoteAddress?: string, remotePort?: number): void;
  
      on(event: "ready", listener: () => void): void;
      on(event: "message", listener: (message: OSCMessage, timeTag?: number) => void): void;
      on(event: "error", listener: (error: Error) => void): void;
  
      off(event: string, listener: (...args: any[]) => void): void;
    }
  
    class SerialPort {
      constructor(options: OSCSocketOptions);
  
      open(): void;
      close(): void;
      send(message: OSCMessage | OSCBundle): void;
  
      on(event: "ready", listener: () => void): void;
      on(event: "message", listener: (message: OSCMessage, timeTag?: number) => void): void;
      on(event: "error", listener: (error: Error) => void): void;
  
      off(event: string, listener: (...args: any[]) => void): void;
    }
  
    export { UDPPort, SerialPort, OSCMessage, OSCBundle, OSCOptions, OSCSocketOptions };
  }
  