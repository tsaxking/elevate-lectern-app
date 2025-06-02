import asyncio


async def test_async_function():
    print("1 Start")
    await asyncio.sleep(1)
    print("1 End")

async def second_loop():
    while True:
        print("2 Start")
        await asyncio.sleep(3)
        print("2 End")

async def async_event_loop():
    while True:
        await test_async_function()
        await asyncio.sleep(2)

async def main():
    asyncio.create_task(second_loop())
    asyncio.create_task(async_event_loop())
    await asyncio.sleep(10)  # Run for a limited time to see the output

if __name__ == "__main__":
    asyncio.run(main())
    print("Main function completed.")