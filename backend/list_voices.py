import asyncio, edge_tts

async def list_voices():
    voices = await edge_tts.list_voices()
    locales = ['de-DE', 'en-US', 'en-GB', 'fr-FR', 'es-ES', 'it-IT', 'pt-BR', 'ja-JP', 'zh-CN', 'ko-KR']
    neural = [v for v in voices if 'Neural' in v['ShortName'] and v['Locale'] in locales]
    print(f"Total voices: {len(voices)}")
    print(f"Neural voices: {len(neural)}\n")
    
    current_locale = None
    for v in sorted(neural, key=lambda x: (x['Locale'], x['Gender'])):
        if v['Locale'] != current_locale:
            current_locale = v['Locale']
            print(f"\n--- {current_locale} ---")
        print(f"  {v['ShortName']} ({v['Gender']})")

asyncio.run(list_voices())
