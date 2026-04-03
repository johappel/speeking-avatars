import asyncio, edge_tts

async def test_short():
    for text in ['Hi', 'A', 'Hallo', 'Test', '123', '']:
        try:
            c = edge_tts.Communicate(text, 'de-DE-KatjaNeural', rate='+0%')
            await c.save(f'F:/code/avatar/speeking/outputs/test_short.mp3')
            print(f'OK: "{text}"')
        except Exception as e:
            print(f'FAIL: "{text}" - {e}')

asyncio.run(test_short())
