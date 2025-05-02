import sensors

def clear():
    print(chr(27) + "[2J")
def main():
    sensor = sensors.Ultrasonic(sensors.UltrasonicConfig(
        echo=20,
        trig=21,
        threading=True,
        tick_speed=15,
        offset=0
    ))
    # A = sensors.Switch(18, False)
    # B = sensors.Switch(24, False)
    while True:
        print(sensor.read())
        # print(A.read())
        # if B.read():
        #     print('B')
        # if not A.read() and not B.read():
        #     print('Not A or B')

main()