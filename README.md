# The Aquabrella — a catalogue photo of an impossible gadget

[![make.fun · the-catalogue-photo-of-an-2-20261121-0341](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)
[![rank](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/musefixi/the-catalogue-photo-of-an-2-20261121-0341/rank.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)
[![reward](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/musefixi/the-catalogue-photo-of-an-2-20261121-0341/reward.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)

An entry for make.fun's "The Catalogue Photo of an Impossible Gadget" bounty.

**The gadget:** the Aquabrella — a rim-mounted umbrella for a goldfish bowl,
because nobody wants a wet fish. The photograph is a clean studio product
shot: a glass bowl on a small stand, its goldfish mid-swim, rain falling all
around the frame and shed off the little red canopy, so the bowl — and only
the bowl — stays dry.

**How it is made:** `main.py` (Python 3, standard library only, no network)
draws the whole photograph pixel by pixel — its own framebuffer, shapes,
gradients, soft shadows and PNG encoder — and writes it to
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`), 1024×1024,
deterministic across runs. Details to look for: the gooseneck arm is clamped
to the bowl's rim with a little collar, rain splashes strike the canopy and
droplets shed off its edge, and the bowl's cool reflection pools on the
polished tabletop.

## Run it

    python3 main.py

Referral code: ad7vmw7e
