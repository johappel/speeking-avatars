import asyncio, edge_tts

async def t():
    c = edge_tts.Communicate('Hallo, ich bin ein Test.', 'de-DE-KatjaNeural', rate='+0%')
    await c.save('F:/code/avatar/speeking/outputs/test_voice.mp3')
    print('OK')

asyncio.run(t())
