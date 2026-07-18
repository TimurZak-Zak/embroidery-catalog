"""Конвертер SVG -> вышивка (контурный/running-stitch стиль).

Берёт SVG (public domain / CC0), достаёт контуры всех фигур, переводит их в
строчку стежков, пишет .vp3 и рисует PNG-превью. Это же ядро конвертера
картинок для этапа 2 (для векторной/контурной графики).

Ограничение честно: контурный стиль. Простые формы/силуэты выходят хорошо,
сложные цветные заливки — нет (заливок пока не делаем).
"""
import io
import math
from pathlib import Path as FsPath

import pyembroidery
from PIL import Image, ImageDraw
from svgelements import Path, Shape, SVG

FIELD_W_MM, FIELD_H_MM = 240.0, 150.0


def _subpaths_points(svg_text: str):
    """Список полилиний (подконтуров) как списки (x, y) в единицах SVG."""
    svg = SVG.parse(io.StringIO(svg_text))
    polylines = []
    for el in svg.elements():
        if not isinstance(el, Shape):
            continue
        try:
            p = Path(el)
            p.reify()  # применить трансформации
        except Exception:
            continue
        for sub in p.as_subpaths():
            try:
                sp = Path(sub)
                length = sp.length(error=1e-3)
            except Exception:
                continue
            if not length or length <= 0:
                continue
            n = max(6, min(600, int(length / 3)))
            pts = []
            for i in range(n + 1):
                try:
                    pt = sp.point(i / n)
                    if pt is not None and math.isfinite(pt.x) and math.isfinite(pt.y):
                        pts.append((pt.x, pt.y))
                except Exception:
                    pass
            if len(pts) >= 2:
                polylines.append(pts)
    return polylines


def _scale_to_mm(polylines, target_mm=95.0):
    xs = [x for pl in polylines for x, _ in pl]
    ys = [y for pl in polylines for _, y in pl]
    if not xs:
        return [], (0, 0)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w = (maxx - minx) or 1
    h = (maxy - miny) or 1
    s = target_mm / max(w, h)
    out = [[((x - minx) * s, (y - miny) * s) for x, y in pl] for pl in polylines]
    return out, (round(w * s, 1), round(h * s, 1))


def _resample(pl, step_mm=1.8):
    """Равномерная строчка ~step_mm между стежками."""
    if len(pl) < 2:
        return pl
    out = [pl[0]]
    acc = 0.0
    prev = pl[0]
    for x, y in pl[1:]:
        seg = math.hypot(x - prev[0], y - prev[1])
        while acc + seg >= step_mm:
            t = (step_mm - acc) / seg
            nx, ny = prev[0] + (x - prev[0]) * t, prev[1] + (y - prev[1]) * t
            out.append((nx, ny))
            prev = (nx, ny)
            seg = math.hypot(x - nx, y - ny)
            acc = 0.0
        acc += seg
        prev = (x, y)
    out.append(pl[-1])
    return out


def convert(svg_text: str, out_vp3: FsPath, out_png: FsPath,
            rgb=0x8A3B3B, target_mm=95.0):
    """Возвращает size_mm dict или None, если не удалось."""
    polylines = _subpaths_points(svg_text)
    if not polylines:
        return None
    scaled, (w, h) = _scale_to_mm(polylines, target_mm)
    if w > FIELD_W_MM or h > FIELD_H_MM:
        s = min(FIELD_W_MM / w, FIELD_H_MM / h) * 0.98
        scaled = [[(x * s, y * s) for x, y in pl] for pl in scaled]
        w, h = round(w * s, 1), round(h * s, 1)
    stitched = [_resample(pl) for pl in scaled]
    total = sum(len(pl) for pl in stitched)
    if total < 10 or total > 25000:
        return None  # мусор или слишком тяжёлое

    # --- .vp3 ---
    pat = pyembroidery.EmbPattern()
    pat.add_thread({"rgb": rgb})
    for pl in stitched:
        pat.add_command(pyembroidery.TRIM)
        first = True
        for x, y in pl:
            cmd = pyembroidery.JUMP if first else pyembroidery.STITCH
            pat.add_stitch_absolute(cmd, x * 10.0, y * 10.0)  # мм -> 0.1мм
            first = False
    pat.add_command(pyembroidery.END)
    pyembroidery.write_vp3(pat, str(out_vp3))

    # --- превью ---
    _thumb(stitched, out_png, rgb)
    return {"w": w, "h": h}


def _thumb(polylines_mm, out_png, rgb):
    W = H = 400
    pad = 36
    col = ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
    xs = [x for pl in polylines_mm for x, _ in pl]
    ys = [y for pl in polylines_mm for _, y in pl]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sw = (maxx - minx) or 1
    sh = (maxy - miny) or 1
    s = min((W - 2 * pad) / sw, (H - 2 * pad) / sh)
    ox = (W - sw * s) / 2
    oy = (H - sh * s) / 2
    img = Image.new("RGB", (W, H), (248, 245, 240))
    d = ImageDraw.Draw(img)
    for pl in polylines_mm:
        scaled = [(ox + (x - minx) * s, oy + (y - miny) * s) for x, y in pl]
        if len(scaled) >= 2:
            d.line(scaled, fill=col, width=3, joint="curve")
    img.save(out_png)
