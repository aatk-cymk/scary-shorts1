"""Procedurally drawn eerie scenes (no outside images). Each returns a 1080x1920 RGB image."""
import random, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 1080, 1920
BLACK = (4, 4, 6)


def sky(seed, top=(10, 12, 22), bottom=(40, 30, 40)):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def moon(img, x, y, r=90, col=(220, 215, 200)):
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], fill=(60, 60, 70))
    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(img)
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    return img


def fog(img, seed, y0=1100, strength=45):
    rnd = random.Random(seed)
    f = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(f)
    for _ in range(30):
        x = rnd.randint(-200, W); y = rnd.randint(y0, H)
        d.ellipse([x, y, x + rnd.randint(300, 700), y + rnd.randint(60, 160)], fill=(strength,) * 3)
    return ImageChops.add(img, f.filter(ImageFilter.GaussianBlur(60)))


def ground(d, y, col=BLACK, seed=0):
    rnd = random.Random(seed)
    pts = [(0, H)]
    for x in range(0, W + 60, 60):
        pts.append((x, y + rnd.randint(-25, 25)))
    pts.append((W, H))
    d.polygon(pts, fill=col)


def dead_tree(d, x, y, h, seed):
    rnd = random.Random(seed)
    def branch(x, y, ang, ln, w):
        if ln < 12 or w < 1:
            return
        x2 = x + math.cos(ang) * ln; y2 = y - math.sin(ang) * ln
        d.line([(x, y), (x2, y2)], fill=BLACK, width=int(w))
        for _ in range(2):
            branch(x2, y2, ang + rnd.uniform(-0.7, 0.7), ln * rnd.uniform(0.6, 0.78), w * 0.65)
    branch(x, y, math.pi / 2 + rnd.uniform(-0.1, 0.1), h * 0.35, h / 22)


def house(d, cx, base, s=1.0, lit=True):
    w, h = 420 * s, 300 * s
    d.rectangle([cx - w / 2, base - h, cx + w / 2, base], fill=BLACK)
    d.polygon([(cx - w / 2 - 30 * s, base - h), (cx, base - h - 220 * s), (cx + w / 2 + 30 * s, base - h)], fill=BLACK)
    d.rectangle([cx + w / 4, base - h - 200 * s, cx + w / 4 + 40 * s, base - h - 60 * s], fill=BLACK)
    if lit:
        for wx in (cx - w / 3, cx + w / 6):
            d.rectangle([wx, base - h * 0.75, wx + 70 * s, base - h * 0.45], fill=(200, 150, 60))


def figure(d, cx, base, s=1.0, col=BLACK):
    d.ellipse([cx - 32 * s, base - 430 * s, cx + 32 * s, base - 360 * s], fill=col)
    d.polygon([(cx - 40 * s, base - 365 * s), (cx + 40 * s, base - 365 * s), (cx + 75 * s, base), (cx - 75 * s, base)], fill=col)


def vignette(img, amt=0.85):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([-W * 0.25, -H * 0.1, W * 1.25, H * 1.1], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(250))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(img, Image.blend(img, dark, amt), m)


def scene_house(seed):
    img = moon(sky(seed), 760, 420)
    d = ImageDraw.Draw(img)
    ground(d, 1350, seed=seed)
    house(d, 540, 1360)
    dead_tree(d, 150, 1380, 900, seed); dead_tree(d, 980, 1390, 700, seed + 1)
    # dirt road
    d.polygon([(470, 1360), (610, 1360), (900, H), (180, H)], fill=(14, 12, 11))
    return vignette(fog(img, seed))


def scene_phone(seed):
    img = sky(seed, (6, 6, 10), (12, 10, 16))
    d = ImageDraw.Draw(img)
    # table
    d.rectangle([0, 1250, W, H], fill=(14, 10, 9))
    # phone glowing
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([290, 700, 790, 1500], fill=(60, 80, 110))
    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(140)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([400, 820, 680, 1360], 40, fill=(10, 10, 12))
    d.rounded_rectangle([418, 850, 662, 1330], 26, fill=(150, 175, 210))
    d.ellipse([500, 960, 580, 1040], fill=(90, 110, 140))
    from PIL import ImageFont
    f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    d.text((540, 1090), "Grandma", fill=(20, 25, 35), font=f1, anchor="mm")
    d.text((540, 1135), "incoming call...", fill=(40, 50, 65), font=f2, anchor="mm")
    d.ellipse([440, 1230, 510, 1300], fill=(160, 30, 30)); d.ellipse([570, 1230, 640, 1300], fill=(30, 140, 60))
    return vignette(img, 0.9)


def scene_grave(seed):
    img = moon(sky(seed, (14, 16, 24), (50, 50, 60)), 300, 380, 70)
    d = ImageDraw.Draw(img)
    ground(d, 1300, seed=seed)
    rnd = random.Random(seed)
    for x, s in [(540, 1.3), (230, 0.8), (860, 0.9), (380, 0.6), (720, 0.6)]:
        w, h = 160 * s, 260 * s
        y = 1320 + rnd.randint(-10, 30)
        d.rectangle([x - w / 2, y - h, x + w / 2, y], fill=(26, 26, 30))
        d.ellipse([x - w / 2, y - h - w / 2, x + w / 2, y - h + w / 2], fill=(26, 26, 30))
    d.line([(540, 900), (540, 1100)], fill=(10, 10, 12), width=14)
    d.line([(480, 960), (600, 960)], fill=(10, 10, 12), width=14)
    dead_tree(d, 950, 1330, 800, seed)
    return vignette(fog(img, seed, 1150, 60))


def scene_door(seed, knock=False):
    img = sky(seed, (8, 7, 8), (16, 13, 12))
    d = ImageDraw.Draw(img)
    # hallway walls
    d.polygon([(0, 0), (300, 500), (300, 1500), (0, H)], fill=(12, 10, 10))
    d.polygon([(W, 0), (780, 500), (780, 1500), (W, H)], fill=(12, 10, 10))
    d.polygon([(0, H), (300, 1500), (780, 1500), (W, H)], fill=(18, 14, 12))
    d.rectangle([380, 620, 700, 1500], fill=(30, 20, 16))
    d.ellipse([650, 1060, 676, 1086], fill=(150, 120, 60))
    # light from under the door
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).rectangle([380, 1490, 700, 1510], fill=(220, 180, 110) if not knock else (190, 40, 30))
    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(18)))
    if knock:
        d = ImageDraw.Draw(img)
        # shadow of two feet under the door
        d.rectangle([460, 1490, 520, 1512], fill=BLACK); d.rectangle([560, 1490, 620, 1512], fill=BLACK)
    return vignette(img, 0.9)


def scene_figure(seed):
    img = moon(sky(seed, (10, 10, 16), (35, 28, 34)), 540, 520, 120, (200, 190, 180))
    d = ImageDraw.Draw(img)
    ground(d, 1400, seed=seed)
    dead_tree(d, 120, 1420, 1000, seed); dead_tree(d, 1000, 1420, 850, seed + 3)
    figure(d, 540, 1410, 1.1)
    return vignette(fog(img, seed, 1250, 55))


def scene_window(seed):
    img = sky(seed, (6, 6, 9), (10, 9, 12))
    d = ImageDraw.Draw(img)
    # window frame showing night outside with a face-like silhouette
    out = moon(sky(seed + 9, (16, 18, 30), (34, 32, 44)), 700, 300, 60)
    od = ImageDraw.Draw(out)
    figure(od, 480, 1700, 1.6)
    out = fog(out, seed, 1300, 60)
    img.paste(out.crop((220, 450, 860, 1450)), (220, 450))
    d = ImageDraw.Draw(img)
    d.rectangle([200, 430, 880, 1470], outline=(20, 16, 14), width=40)
    d.line([(540, 450), (540, 1450)], fill=(20, 16, 14), width=26)
    d.line([(220, 950), (860, 950)], fill=(20, 16, 14), width=26)
    return vignette(img, 0.85)


SCENES = {
    "house": scene_house, "phone": scene_phone, "grave": scene_grave,
    "door": scene_door, "knock": lambda s: scene_door(s, True),
    "figure": scene_figure, "window": scene_window,
}


def draw(name, seed):
    return SCENES[name](seed)
