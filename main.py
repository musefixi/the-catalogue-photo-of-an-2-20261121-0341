#!/usr/bin/env python3
"""Catalogue photograph of an impossible gadget: the Aquabrella.

A studio product shot, drawn pixel by pixel with the Python standard
library alone: a glass fishbowl on a small stand, its goldfish kept dry
in the rain by a little umbrella mounted on the bowl's rim. The rain
falls everywhere except on the fish.

Writes entry.png to $MAKEFUN_OUTPUT_DIR (default /output).
"""

import math
import os
import random
import zlib
from pathlib import Path

SS = 2                      # supersampling factor
W = H = 1024                # final size
RW, RH = W * SS, H * SS     # render size

fb = bytearray(RW * RH * 3)


def _idx(x, y):
    return (y * RW + x) * 3


def put(x, y, rgb):
    if 0 <= x < RW and 0 <= y < RH:
        i = _idx(x, y)
        fb[i] = rgb[0]
        fb[i + 1] = rgb[1]
        fb[i + 2] = rgb[2]


def blend(x, y, rgb, a):
    if 0 <= x < RW and 0 <= y < RH and a > 0.0:
        i = _idx(x, y)
        ia = 1.0 - a
        fb[i] = int(fb[i] * ia + rgb[0] * a)
        fb[i + 1] = int(fb[i + 1] * ia + rgb[1] * a)
        fb[i + 2] = int(fb[i + 2] * ia + rgb[2] * a)


def hspan(x0, x1, y, rgb, a=1.0):
    """Solid horizontal run, fast path for opaque colour."""
    if y < 0 or y >= RH:
        return
    x0 = max(0, x0)
    x1 = min(RW - 1, x1)
    if x1 < x0:
        return
    if a >= 1.0:
        i = _idx(x0, y)
        n = (x1 - x0 + 1) * 3
        fb[i:i + n] = bytes(rgb) * (x1 - x0 + 1)
    else:
        for x in range(x0, x1 + 1):
            blend(x, y, rgb, a)


def mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def ellipse(cx, cy, rx, ry, rgb, a=1.0):
    cx, cy, rx, ry = cx * SS, cy * SS, rx * SS, ry * SS
    y0, y1 = int(cy - ry), int(cy + ry)
    for y in range(y0, y1 + 1):
        t = (y - cy) / ry
        if abs(t) > 1:
            continue
        dx = rx * math.sqrt(1 - t * t)
        hspan(int(cx - dx), int(cx + dx), y, rgb, a)


def ellipse_grad(cx, cy, rx, ry, top, bottom):
    """Ellipse with a vertical colour gradient."""
    cx, cy, rx, ry = cx * SS, cy * SS, rx * SS, ry * SS
    y0, y1 = int(cy - ry), int(cy + ry)
    for y in range(y0, y1 + 1):
        t = (y - cy) / ry
        if abs(t) > 1:
            continue
        dx = rx * math.sqrt(1 - t * t)
        f = (y - y0) / max(1, (y1 - y0))
        hspan(int(cx - dx), int(cx + dx), y, mix(top, bottom, f))


def circle(cx, cy, r, rgb, a=1.0):
    ellipse(cx, cy, r, r, rgb, a)


def ring(cx, cy, r, width, rgb, a=1.0):
    cx, cy, r, width = cx * SS, cy * SS, r * SS, width * SS
    y0, y1 = int(cy - r - width), int(cy + r + width)
    for y in range(y0, y1 + 1):
        for x in range(int(cx - r - width), int(cx + r + width) + 1):
            d = math.hypot(x - cx, y - cy)
            if abs(d - r) <= width / 2:
                blend(x, y, rgb, a)


def poly(points, rgb, a=1.0):
    pts = [(x * SS, y * SS) for x, y in points]
    ys = [p[1] for p in pts]
    y0, y1 = int(min(ys)), int(max(ys))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, yy1 = pts[i]
            x2, yy2 = pts[(i + 1) % n]
            if (yy1 <= y < yy2) or (yy2 <= y < yy1):
                xs.append(x1 + (y - yy1) * (x2 - x1) / (yy2 - yy1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            hspan(int(xs[i]), int(xs[i + 1]), y, rgb, a)


def thick_line(p0, p1, width, rgb, a=1.0):
    steps = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1])) * SS) + 1
    for s in range(steps + 1):
        t = s / steps
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        circle(x, y, width / 2, rgb, a)


def thick_arc(cx, cy, r, a0, a1, width, rgb, alpha=1.0):
    steps = int(abs(a1 - a0) * r * SS) + 1
    for s in range(steps + 1):
        t = a0 + (a1 - a0) * s / steps
        x = cx + r * math.cos(t)
        y = cy + r * math.sin(t)
        circle(x, y, width / 2, rgb, alpha)


def soft_shadow(cx, cy, rx, ry, strength=0.34):
    """Elliptical shadow with radial falloff."""
    cx, cy, rx, ry = cx * SS, cy * SS, rx * SS, ry * SS
    y0, y1 = int(cy - ry), int(cy + ry)
    for y in range(y0, y1 + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 1:
                blend(x, y, (38, 34, 30), strength * (1 - d) ** 1.4)


# ---------------------------------------------------------------- backdrop
def backdrop():
    top, mid, floor_a, floor_b = (246, 243, 238), (232, 226, 216), (224, 216, 203), (203, 193, 178)
    horizon = int(RH * 0.735)
    for y in range(RH):
        if y < horizon:
            c = mix(top, mid, y / horizon)
        else:
            c = mix(floor_a, floor_b, (y - horizon) / (RH - horizon))
        hspan(0, RW - 1, y, c)
    # soft pool of light behind the product
    cx, cy = RW // 2, int(RH * 0.44)
    for y in range(int(RH * 0.05), int(RH * 0.85)):
        for x in range(int(RW * 0.08), int(RW * 0.92)):
            d = ((x - cx) / (RW * 0.46)) ** 2 + ((y - cy) / (RH * 0.42)) ** 2
            if d < 1:
                blend(x, y, (255, 252, 246), 0.20 * (1 - d))


# ---------------------------------------------------------------- the stand
def stand():
    # floor shadow first
    soft_shadow(512, 852, 268, 34, 0.30)
    # base
    ellipse_grad(512, 838, 118, 20, (120, 124, 130), (74, 78, 84))
    ellipse(512, 830, 118, 18, (168, 172, 178))
    # chrome pole
    for x in range(int(498 * SS), int(526 * SS) + 1):
        t = (x / SS - 498) / 28
        c = mix((96, 100, 106), (216, 220, 224), math.sin(t * math.pi) ** 1.5)
        for y in range(int(706 * SS), int(832 * SS)):
            put(x, y, c)
    # wooden table top
    ellipse_grad(512, 706, 216, 34, (146, 104, 70), (110, 74, 46))
    ellipse_grad(512, 698, 216, 32, (178, 132, 90), (148, 106, 72))
    ellipse(512, 694, 150, 20, (190, 146, 102), 0.5)
    # contact shadow of the bowl on the wood
    soft_shadow(512, 700, 168, 22, 0.26)
    # the bowl's cool reflection pooled on the polished wood
    ellipse(512, 708, 118, 12, (196, 220, 226), 0.16)


# ---------------------------------------------------------------- the bowl
BX, BY, BR = 512, 516, 186  # bowl centre and radius


def in_bowl(x, y, shrink=0):
    return math.hypot(x - BX, y - BY) <= BR - shrink


def bowl_back():
    # glass body: pale tint disc
    ellipse_grad(BX, BY, BR, BR, (226, 238, 240), (198, 216, 222))
    # water: below a gentle wave line
    rng = random.Random(7)
    for y in range(int((BY - BR) * SS), int((BY + BR) * SS)):
        fy = y / SS
        wave = BY - 44 + 5 * math.sin((fy) * 0.0 + (y / SS) * 0.0)  # placeholder
        xs = []
        dx2 = BR * BR - (fy - BY) ** 2
        if dx2 < 0:
            continue
        dx = math.sqrt(dx2)
        xs = (BX - dx, BX + dx)
        if fy > BY - 46 + 4 * math.sin(fy * 0.05):
            t = (fy - (BY - 46)) / (2 * BR - 46)
            c = mix((186, 226, 234), (116, 178, 198), max(0.0, min(1.0, t)))
            hspan(int(xs[0] * SS) + 2, int(xs[1] * SS) - 2, y, c)
    # gravel bed
    for y in range(int((BY + 118) * SS), int((BY + BR - 4) * SS)):
        fy = y / SS
        dx2 = (BR - 4) ** 2 - (fy - BY) ** 2
        if dx2 < 0:
            continue
        dx = math.sqrt(dx2)
        hspan(int((BX - dx) * SS), int((BX + dx) * SS), y, (206, 188, 158))
    rng = random.Random(11)
    for _ in range(240):
        gx = BX + rng.uniform(-150, 150)
        gy = BY + 128 + rng.uniform(0, 46) * (1 - (abs(gx - BX) / 190) ** 2)
        if in_bowl(gx, gy, 10):
            circle(gx, gy, rng.uniform(2.5, 5.5),
                   rng.choice([(176, 152, 116), (222, 204, 172), (150, 128, 96)]))
    # a little plant
    for k, sway in enumerate((-16, -6, 4, 14)):
        pts = []
        for s in range(21):
            t = s / 20
            pts.append((424 + sway * t * t + 6 * math.sin(t * 5 + k), 668 - 96 * t))
        for i in range(len(pts) - 1):
            thick_line(pts[i], pts[i + 1], 7 - 3 * (i / 20), (74, 138, 84))


def fish():
    cx, cy = 548, 548
    # tail
    poly([(cx - 38, cy), (cx - 78, cy - 30), (cx - 70, cy), (cx - 78, cy + 30)],
         (224, 118, 26))
    # body
    ellipse_grad(cx, cy, 56, 31, (250, 176, 60), (232, 124, 22))
    ellipse(cx - 6, cy + 12, 44, 16, (252, 205, 130), 0.45)   # belly light
    # dorsal fin
    poly([(cx - 12, cy - 26), (cx + 10, cy - 40), (cx + 18, cy - 24)], (224, 118, 26))
    # eye
    circle(cx + 38, cy - 7, 5.2, (30, 26, 24))
    circle(cx + 39.5, cy - 8.5, 1.8, (255, 255, 255))
    # gill arc
    thick_arc(cx + 22, cy, 20, -1.1, 1.1, 2.6, (196, 96, 16), 0.8)
    # bubbles
    for bx, by, br in ((618, 470, 6), (630, 442, 4.4), (612, 416, 3.2), (640, 486, 3.6)):
        ring(bx, by, br, 1.6, (240, 250, 252), 0.75)
        circle(bx - br * 0.3, by - br * 0.3, br * 0.28, (255, 255, 255), 0.8)


def bowl_front():
    # water surface line
    pts = []
    for x in range(BX - BR + 14, BX + BR - 13):
        pts.append((x, BY - 46 + 4 * math.sin(x * 0.05)))
    for i in range(len(pts) - 1):
        thick_line(pts[i], pts[i + 1], 2.4, (238, 250, 252), 0.85)
    # glass rim: a flat, faint opening ellipse tucked inside the outline
    ellipse(BX, BY - BR + 12, BR - 30, 11, (214, 230, 234), 0.32)
    # bowl outline + glass shading
    ring(BX, BY, BR, 3.4, (250, 253, 254), 0.65)
    ring(BX, BY, BR - 5, 1.6, (160, 190, 200), 0.35)
    # big soft highlight, upper left
    for y in range(int((BY - 150) * SS), int((BY + 30) * SS)):
        for x in range(int((BX - 168) * SS), int((BX - 40) * SS)):
            fx, fy = x / SS, y / SS
            d = (((fx - (BX - 108)) / 44) ** 2 + ((fy - (BY - 62)) / 92) ** 2)
            if d < 1 and in_bowl(fx, fy, 4):
                blend(x, y, (255, 255, 255), 0.30 * (1 - d))
    # small bright streak
    thick_arc(BX, BY, BR - 16, math.radians(150), math.radians(196), 7, (255, 255, 255), 0.5)
    # bottom reflection
    ellipse(BX, BY + BR - 26, 84, 16, (255, 255, 255), 0.20)


# ---------------------------------------------------------------- umbrella
def umbrella():
    # mounting arm: a gooseneck clamped to the bowl's top-right rim,
    # curving up to the canopy's underside
    p0 = (632, 378)          # clamp point on the rim
    p1 = (706, 316)          # control: bows out past the glass
    p2 = (628, 240)          # meets the canopy underside
    pts = []
    for s in range(61):
        t = s / 60
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    for i in range(len(pts) - 1):
        thick_line(pts[i], pts[i + 1], 8, (88, 92, 98))
    for i in range(len(pts) - 1):
        thick_line((pts[i][0] - 1.6, pts[i][1]), (pts[i + 1][0] - 1.6, pts[i + 1][1]),
                   3, (205, 209, 213))
    # the clamp: a small collar gripping the rim
    ellipse(632, 378, 13, 9, (70, 74, 80))
    ellipse(630, 376, 8, 5, (150, 154, 160))
    # canopy: dome with alternating segments and a scalloped hem
    cx, cy, rx, ry = 512, 238, 272, 118
    nseg = 8
    for sgm in range(nseg):
        a0 = math.pi + sgm * math.pi / nseg
        a1 = math.pi + (sgm + 1) * math.pi / nseg
        col = (224, 84, 66) if sgm % 2 == 0 else (198, 62, 50)
        steps = 26
        wedge = [(cx, cy)]
        for s in range(steps + 1):
            t = a0 + (a1 - a0) * s / steps
            wedge.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
        poly(wedge, col)
    # scalloped hem: cream underside arcs
    for sgm in range(nseg):
        t = (sgm + 0.5) / nseg
        hx = cx - rx + 2 * rx * t
        ellipse(hx, cy - 1, rx / nseg * 0.48, 10, (246, 231, 210))
    ellipse(cx, cy, rx, 10, (250, 240, 224), 0.9)
    # dome shading: light from upper left
    for y in range(int((cy - ry) * SS), int(cy * SS)):
        for x in range(int((cx - rx) * SS), int((cx + rx) * SS)):
            fx, fy = x / SS, y / SS
            d = (((fx - (cx - 96)) / 190) ** 2 + ((fy - (cy - 66)) / 74) ** 2)
            if d < 1:
                blend(x, y, (255, 226, 200), 0.20 * (1 - d))
    # seams
    for sgm in range(1, nseg):
        a = math.pi + sgm * math.pi / nseg
        thick_line((cx, cy - 4), (cx + rx * math.cos(a), cy + ry * math.sin(a)),
                   2.2, (150, 44, 38), 0.55)
    # finial
    thick_line((cx, cy - ry + 4), (cx, cy - ry - 22), 5, (88, 92, 98))
    circle(cx, cy - ry - 26, 7, (224, 84, 66))


# ---------------------------------------------------------------- rain
def rain():
    rng = random.Random(23)
    col = (148, 178, 198)
    # falling streaks everywhere except the dry cone under the canopy
    for _ in range(300):
        x = rng.uniform(8, 1016)
        y = rng.uniform(6, 560)
        ln = rng.uniform(14, 26)
        if 238 - 6 < x < 786 and y > 96 and y < 560 and (y - 238) > -((x - 512) ** 2) * 0.0 - 0:
            # under the canopy's shelter: skip streaks below the dome line
            dome_y = 238 - 118 * math.sqrt(max(0.0, 1 - ((x - 512) / 272) ** 2)) if abs(x - 512) < 272 else 999
            if y > dome_y - 6:
                continue
        thick_line((x, y), (x - ln * 0.28, y + ln), 2.0, col, rng.uniform(0.25, 0.5))
    # splashes on the canopy + droplets shed off its edge
    for _ in range(46):
        x = rng.uniform(268, 756)
        dome_y = 238 - 118 * math.sqrt(max(0.0, 1 - ((x - 512) / 272) ** 2))
        thick_line((x - 5, dome_y - 8), (x, dome_y - 1), 1.8, (235, 246, 250), 0.8)
        thick_line((x + 5, dome_y - 8), (x, dome_y - 1), 1.8, (235, 246, 250), 0.8)
    for _ in range(26):
        side = rng.choice([-1, 1])
        x = 512 + side * rng.uniform(238, 272)
        y = rng.uniform(216, 250)
        thick_line((x, y), (x + side * rng.uniform(8, 16), y + rng.uniform(8, 15)),
                   1.8, col, 0.55)


def vignette():
    cx, cy = RW / 2, RH / 2
    for y in range(0, RH, 2):
        for x in range(0, RW, 2):
            d = ((x - cx) / (RW * 0.78)) ** 2 + ((y - cy) / (RH * 0.78)) ** 2
            if d > 0.55:
                a = min(0.16, (d - 0.55) * 0.22)
                for dy in (0, 1):
                    for dx in (0, 1):
                        blend(x + dx, y + dy, (52, 48, 44), a)


def render():
    backdrop()
    rain()          # rain behind the product reads at the edges
    stand()
    bowl_back()
    fish()
    bowl_front()
    umbrella()
    rain()          # and a second, nearer layer
    vignette()
    # downscale 2x2
    out = bytearray(W * H * 3)
    for y in range(H):
        for x in range(W):
            i = _idx(x * SS, y * SS)
            j = (y * W + x) * 3
            for c in range(3):
                out[j + c] = (fb[i + c] + fb[i + 3 + c] +
                              fb[i + RW * 3 + c] + fb[i + RW * 3 + 3 + c]) // 4
    return out


def write_png(pixels, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += pixels[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        c = zlib.crc32(tag)
        c = zlib.crc32(data, c)
        return (len(data).to_bytes(4, "big") + tag + data +
                (c & 0xFFFFFFFF).to_bytes(4, "big"))

    ihdr = (W.to_bytes(4, "big") + H.to_bytes(4, "big") +
            bytes([8, 2, 0, 0, 0]))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    Path(path).write_bytes(png)
    return len(png)


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    size = write_png(render(), out_dir / "entry.png")
    print(f"entry.png: {size} bytes, {W}x{H}")


if __name__ == "__main__":
    main()
