from system import System, SYSTEM_STATE
import inquirer
import asyncio
import globals

class CLI:
    def __init__(self, system: System):
        self.system = system

        asyncio.create_task(self.run())

    async def run(self):
        questions = [
            inquirer.List(
                "action",
                message="Choose an action",
                choices=[
                    "Move Up",
                    "Move Down",
                    "Stop",
                    "Go To",
                    "Calibrate",
                    "Shutdown",
                ]
            )
        ]

        while True:
            response = inquirer.prompt(questions)
            if response["action"] == "Move Up":
                speed = float(input("Enter speed: "))
                self.system.send_command("move", speed)

            if response["action"] == "Move Down":
                speed = float(input("Enter speed: "))
                self.system.send_command("move", -speed)

            if response["action"] == "Stop":
                self.system.send_command("stop")

            if response["action"] == "Go To":
                position = float(input("Enter position: "))
                self.system.send_command("go_to", position)

            if response["action"] == "Calibrate":
                self.system.send_command("calibrate")

            if response["action"] == "Shutdown":
                self.system.send_command("shutdown")
                break


if __name__ == "__main__":
    try:
        cli = CLI(globals.SYSTEM)
    except KeyboardInterrupt:
        pass
    finally:
        globals.SYSTEM.shutdown()
        print("Goodbye!")