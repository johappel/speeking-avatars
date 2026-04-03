import asyncio, edge_tts

async def lv():
    voices = await edge_tts.list_voices()
    for v in voices:
        print(f"{v['ShortName']} - {v['Gender']} - {v['Locale']}")

asyncio.run(lv())
