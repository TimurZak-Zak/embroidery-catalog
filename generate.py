"""Генератор стартового набора простых вышивальных дизайнов.

Создаёт:
  designs/<slug>.vp3   — валидный файл вышивки (running stitch)
  thumbs/<slug>.png    — превью
  catalog.json         — каталог для приложения

Это ВРЕМЕННЫЙ seed, чтобы приложение работало end-to-end. Реальную
кураторскую подборку из легальных источников добавим позже.
Формы — простые примитивы (по сути общественное достояние).
"""
import json
import math
from pathlib import Path

import pyembroidery
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
DESIGNS = ROOT / "designs"
THUMBS = ROOT / "thumbs"
DESIGNS.mkdir(exist_ok=True)
THUMBS.mkdir(exist_ok=True)

RAW = "https://raw.githubusercontent.com/TimurZak-Zak/embroidery-catalog/main"

# --- геометрия форм: возвращают список точек (x, y) в мм ---


def heart(size=70, n=220):
    pts = []
    for i in range(n + 1):
        t = math.pi * 2 * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x, -y))
    return _fit(pts, size)


def star(points=5, size=70, n=None):
    n = n or points * 2
    pts = []
    for i in range(n + 1):
        ang = math.pi / 2 + 2 * math.pi * i / n
        r = 1.0 if i % 2 == 0 else 0.42
        pts.append((r * math.cos(ang), -r * math.sin(ang)))
    return _fit(pts, size)


def snowflake(size=80):
    pts = []
    for arm in range(6):
        a = math.pi / 3 * arm
        dx, dy = math.cos(a), math.sin(a)
        px, py = math.cos(a + math.pi / 6) * 0.3, math.sin(a + math.pi / 6) * 0.3
        pts.append((0, 0))
        pts.append((dx, dy))
        pts.append((dx * 0.6 + px, dy * 0.6 + py))  # веточка
        pts.append((dx * 0.6, dy * 0.6))
        pts.append((dx * 0.6 - px, dy * 0.6 - py))
        pts.append((dx * 0.6, dy * 0.6))
        pts.append((0, 0))
    return _fit(pts, size)


def circle(size=60, n=120):
    pts = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
    return _fit(pts, size)


def rose(k=4, size=80, n=360):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        r = math.cos(k * t)
        pts.append((r * math.cos(t), r * math.sin(t)))
    return _fit(pts, size)


def polygon(sides=6, size=65):
    pts = []
    for i in range(sides + 1):
        a = math.pi / 2 + 2 * math.pi * i / sides
        pts.append((math.cos(a), math.sin(a)))
    return _fit(pts, size)


def spiral(turns=4, size=75, n=300):
    pts = []
    for i in range(n + 1):
        t = turns * 2 * math.pi * i / n
        r = i / n
        pts.append((r * math.cos(t), r * math.sin(t)))
    return _fit(pts, size)


def wave_border(width=180, height=25, waves=6, n=240):
    pts = []
    for i in range(n + 1):
        x = i / n
        y = math.sin(waves * 2 * math.pi * x)
        pts.append((x * 2 - 1, y))
    return _fit(pts, max(width, height), keep_aspect=(width, height))


def flower_petals(petals=8, size=85, n=400):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        r = 0.5 + 0.5 * abs(math.sin(petals / 2 * t))
        pts.append((r * math.cos(t), r * math.sin(t)))
    return _fit(pts, size)


def _fit(pts, size, keep_aspect=None):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs) or 1
    h = max(ys) - min(ys) or 1
    if keep_aspect:
        tw, th = keep_aspect
        sx, sy = tw / w, th / h
    else:
        s = size / max(w, h)
        sx = sy = s
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2
    return [((x - cx) * sx, (y - cy) * sy) for x, y in pts]


# --- запись .vp3 и превью ---


def save_design(slug, pts_mm, rgb):
    p = pyembroidery.EmbPattern()
    p.add_thread({"rgb": rgb})
    for x, y in pts_mm:
        p.add_stitch_absolute(pyembroidery.STITCH, x * 10.0, y * 10.0)  # мм -> 0.1мм
    p.add_command(pyembroidery.END)
    pyembroidery.write_vp3(p, str(DESIGNS / f"{slug}.vp3"))
    _thumb(slug, pts_mm, rgb)


def _rgb_tuple(rgb):
    return ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)


def _thumb(slug, pts_mm, rgb):
    W = H = 400
    pad = 40
    img = Image.new("RGB", (W, H), (248, 245, 240))
    d = ImageDraw.Draw(img)
    rgb = _rgb_tuple(rgb)
    xs = [p[0] for p in pts_mm]
    ys = [p[1] for p in pts_mm]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sw = (maxx - minx) or 1
    sh = (maxy - miny) or 1
    s = min((W - 2 * pad) / sw, (H - 2 * pad) / sh)
    ox = (W - sw * s) / 2
    oy = (H - sh * s) / 2
    scaled = [(ox + (x - minx) * s, oy + (y - miny) * s) for x, y in pts_mm]
    d.line(scaled, fill=rgb, width=3, joint="curve")
    img.save(THUMBS / f"{slug}.png")


# --- набор дизайнов ---

RED = 0xD1495B
GOLD = 0xE0A458
BLUE = 0x5B8FB9
GREEN = 0x6A994E
PINK = 0xE07A9B
PURPLE = 0x8367C7
TEAL = 0x2A9D8F

ITEMS = [
    ("heart-70", "Сердечко", "Сердечки", heart(70), RED),
    ("heart-100", "Большое сердце", "Сердечки", heart(100), PINK),
    ("star5", "Звезда", "Звёзды", star(5, 70), GOLD),
    ("star6", "Шестиконечная звезда", "Звёзды", star(6, 75), GOLD),
    ("snowflake", "Снежинка", "Зима", snowflake(85), BLUE),
    ("circle", "Круг", "Фигуры", circle(60), TEAL),
    ("hexagon", "Шестиугольник", "Фигуры", polygon(6, 65), GREEN),
    ("triangle", "Треугольник", "Фигуры", polygon(3, 65), PURPLE),
    ("rose4", "Розетка", "Цветы", rose(4, 80), PINK),
    ("rose5", "Цветок", "Цветы", rose(5, 80), RED),
    ("flower8", "Ромашка", "Цветы", flower_petals(8, 90), GOLD),
    ("spiral", "Спираль", "Узоры", spiral(4, 75), TEAL),
    ("wave", "Волнистый бордюр", "Бордюры", wave_border(190, 28, 6), BLUE),
    ("pentagon", "Пятиугольник", "Фигуры", polygon(5, 65), GREEN),
]


def main():
    catalog = []
    for slug, name, category, pts, rgb in ITEMS:
        save_design(slug, pts, rgb)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w = round(max(xs) - min(xs), 1)
        h = round(max(ys) - min(ys), 1)
        catalog.append(
            {
                "id": slug,
                "name": name,
                "category": category,
                "size_mm": {"w": w, "h": h},
                "thumbnail": f"{RAW}/thumbs/{slug}.png",
                "file_url": f"{RAW}/designs/{slug}.vp3",
                "license": "Public Domain",
                "author": "Embroidery Studio",
            }
        )
    (ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), "utf-8"
    )
    print(f"Сгенерировано дизайнов: {len(catalog)}")


if __name__ == "__main__":
    main()
