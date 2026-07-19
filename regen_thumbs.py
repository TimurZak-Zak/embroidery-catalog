"""Перерисовывает ВСЕ превью в единый премиум-стиль:
монохромная строчка одного благородного цвета на тёплом paper-фоне с тонкой рамкой —
как каталог образцов ателье, а не разноцветные детские каракули.

Рендерит из самих .vp3 (designs/*.vp3), перезаписывает thumbs/*.png тем же именем,
поэтому ссылки в catalog.json остаются прежними.
"""
from pathlib import Path

import pyembroidery
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
DESIGNS = ROOT / "designs"
THUMBS = ROOT / "thumbs"
THUMBS.mkdir(exist_ok=True)

SIZE = 480
SS = 2  # суперсэмплинг для гладких линий
PAD = 64
INK = (74, 42, 48)        # глубокий чернильно-бордовый — один на всё, сдержанно
PAPER = (243, 239, 231)   # тёплый off-white
FRAME = (222, 214, 200)   # тонкая рамка
LINE_W = 3


def _polylines(vp3: Path):
    pat = pyembroidery.read(str(vp3))
    out, cur = [], []
    for st in pat.stitches:
        x, y, cmd = st[0], st[1], st[2]
        if cmd == pyembroidery.STITCH:
            cur.append((x, y))
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = []
    if len(cur) >= 2:
        out.append(cur)
    return out


def render(vp3: Path, out: Path):
    polys = _polylines(vp3)
    if not polys:
        return False
    xs = [x for pl in polys for x, _ in pl]
    ys = [y for pl in polys for _, y in pl]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w = (maxx - minx) or 1
    h = (maxy - miny) or 1
    S = SIZE * SS
    pad = PAD * SS
    s = min((S - 2 * pad) / w, (S - 2 * pad) / h)
    ox = (S - w * s) / 2
    oy = (S - h * s) / 2

    img = Image.new("RGB", (S, S), PAPER)
    d = ImageDraw.Draw(img)
    # тонкая внутренняя рамка
    m = 10 * SS
    d.rectangle([m, m, S - m, S - m], outline=FRAME, width=1 * SS)
    for pl in polys:
        pts = [(ox + (x - minx) * s, oy + (y - miny) * s) for x, y in pl]
        if len(pts) >= 2:
            d.line(pts, fill=INK, width=LINE_W * SS, joint="curve")
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img.save(out)
    return True


def main():
    n = 0
    for vp3 in sorted(DESIGNS.glob("*.vp3")):
        if render(vp3, THUMBS / f"{vp3.stem}.png"):
            n += 1
    print(f"Перерисовано превью: {n}")


if __name__ == "__main__":
    main()
