{#snippet point(name)}
    <span class="text-info">{`{${name}}`}</span>
{/snippet}


<div class="container">
    <div class="row mb-3">
        <h1>Documentation</h1>
    </div>
    <div class="row mb-3">
        <div class="col">
            <p>
                Here is the documentation for the OSC and TCP protocols, which is used to control the lectern and future teleprompter states.
            </p>
        </div>
    </div>
    <div class="row mb-3">
        <div class="col">
            <h2>
                OSC Endpoints
            </h2>
            <br>
            <p>
                These endpoints will be executed in the order they are received, so if you send multiple commands, they will be executed sequentially. This includes the /stop command, if there is a command in the queue that takes time (like /go_to), the /stop command will not interrupt it.
            </p>
        </div>
    </div>
    <div class="row mb-3">
        <div class="col">
            <ul>
                <li>
                    <strong>/lectern/bump/{@render point('distance')}</strong> - Bump the lectern by a specified distance in inches
                </li>
                <li>
                    <strong>/lectern/move/{@render point('speed')}</strong> - Move the lectern at a specified speed in % of max motor speed (-1 to 1)
                </li>
                <li>
                    <strong>/lectern/stop</strong> - Stop the lectern movement (use with /move)
                    <br>
                    <small class="text-muted">
                        *Note: This may not stop movement immediately if there are commands that take time. Please use the TCP protocol for full system stop.
                    </small>
                </li>
                <li>
                    <strong>/lectern/go_to/{@render point('position')}</strong> - Move the lectern to a specified position in inches
                </li>
                <li>
                    <strong>
                        /lectern/go_to/{@render point('position')}/in/{@render point('time')}</strong> - Move the lectern to a specified position in inches over a specified time in seconds 
                        <br>
                        <small class="text-muted">
                            *Note: This will not exceed the maximum speed of the motors, so if the time is too short, the actual movement may be slower than requested.
                        </small>
                </li>
                <li>
                    <strong>/lectern/calibrate</strong> - Runs the lectern calibration sequence
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/bump/{@render point('distance')}</strong> - Bump the teleprompter by a specified distance in inches
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/move/{@render point('speed')}</strong> - Move the teleprompter at a specified speed in % of max motor speed (-1 to 1)
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/go_to/{@render point('position')}</strong> - Move the teleprompter to a specified position in inches
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/go_to/{@render point('position')}/in/{@render point('time')}</strong> - Move the teleprompter to a specified position in inches over a specified time in seconds
                    <br>
                    <small class="text-muted">
                        *Note: This will not exceed the maximum speed of the motors, so if the time is too short, the actual movement may be slower than requested.
                    </small>
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/stop</strong> - Stop the teleprompter movement
                    <br>
                    <small class="text-muted">
                        *Note: This may not stop movement immediately if there are commands that take time. Please use the TCP protocol for full system stop.
                    </small>
                </li>
                <li>
                    <strong>/bump/{@render point('distance')}</strong> - Bump all systems by a specified distance in inches
                </li>
                <li>
                    <strong>/move/{@render point('speed')}</strong> - Move all systems at a specified speed in % of max motor speed (-1 to 1)
                </li>
                <li>
                    <strong>/go_to/{@render point('position')}</strong> - Move all systems to a specified position in inches
                </li>
                <li>
                    <strong>/go_to/{@render point('position')}/in/{@render point('time')}</strong> - Move all systems to a specified position in inches over a specified time in seconds
                    <br>
                    <small class="text-muted">
                        *Note: This will not exceed the maximum speed of the motors, so if the time is too short, the actual movement may be slower than requested.
                    </small>
                </li>
                <li>
                    <strong>/stop</strong> - Stop all movement
                    <br>
                    <small class="text-muted">
                        *Note: This may not stop movement immediately if there are commands that take time. Please use the TCP protocol for full system stop.
                    </small>
                </li>
            </ul>
        </div>
    </div>
    <div class="row mb-3">
        <div class="col">
            <h2>
                TCP Endpoints
            </h2>
            <br>
            <p>
                The TCP protocol is used to bypass the OSC queue and immediately. The usage of these clears the OSC Queue and attempts to stop the current command.
            </p>
        </div>
    </div>
    <div class="row mb-3">
        <div class="col">
            <ul>
                <li>
                    <strong>/stop</strong> - Stop all movement immediately
                </li>
                <li>
                    <strong>/lectern/stop</strong> - Stop the lectern movement immediately
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/stop</strong> - Stop the teleprompter movement immediately
                </li>
                <li>
                    <strong>/reboot</strong> - Reboot all systems immediately
                </li>
                <li>
                    <strong>/lectern/reboot</strong> - Reboot the lectern system immediately
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/reboot</strong> - Reboot the teleprompter system immediately
                </li>
                <li>
                    <strong>/home</strong> - Moves all systems to their home position
                </li>
                <li>
                    <strong>/lectern/home</strong> - Moves the lectern to its home position
                </li>
                <li>
                    <strong>/teleprompter/{@render point('id')}/home</strong> - Moves the teleprompter to its home position
                </li>
                <li>
                    <strong>/system_reboot</strong> - Shutdown the raspberry pi and reboots it
                </li>
                <li>
                    <strong>/reboot_tcp</strong> - Restarts the TCP server
                </li>
                <li>
                    <strong>/reboot_osc</strong> - Restarts the OSC server
                </li>
                <li>
                    <strong>/lectern/manual_speed/{@render point('speed')}</strong> - Set the manual speed of the lectern in % of max motor speed (0 to 1)
                </li>
            </ul>
        </div>
    </div>
</div>