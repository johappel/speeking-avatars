import asyncio, edge_tts

text = """Es war einmal ein mutiges und kluges Eichhörnchen namens Svenja, das in einem wunderschönen Wald lebte.

Svenja war im ganzen Wald für ihr schnelles Denken und ihre Tapferkeit bekannt.

Und ebenso war sie immer bereit, ihren Freunden in der Not zu helfen.

Eines Tages war Svenja unterwegs, um Nüsse für den Winter zu sammeln, als sie ein seltsames Geräusch hörte, das von einem nahen Baum kam.

Sie kletterte auf den Baum, um nachzusehen, was da los war.

Dann sah sie eine Gruppe fieser Vögel, die einen kleinen, hilflosen Vogel ärgerten.

Svenja war sofort klar, dass sie eingreifen musste."""

async def test():
    c = edge_tts.Communicate(text, 'de-DE-KatjaNeural', rate='+0%')
    await c.save('F:/code/avatar/speeking/outputs/test_svenja.mp3')
    print('OK - saved')

asyncio.run(test())
