import asyncio, edge_tts

async def test_rate():
    for rate in ['-20%', '-10%', '+0%', '+10%', '+20%']:
        try:
            c = edge_tts.Communicate('Hallo Welt', 'de-DE-KatjaNeural', rate=rate)
            await c.save(f'F:/code/avatar/speeking/outputs/test_{rate.replace("+","p").replace("-","m")}.mp3')
            print(f'OK: {rate}')
        except Exception as e:
            print(f'FAIL: {rate} - {e}')

asyncio.run(test_rate())
