"""Переносит выбранные staging2-кандидаты в каталог с русскими именами.
Выброшены: alcohol-glass-beer-tulip (#20), ten-year-society (#31), stanley-hawk (#35).
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "staging2"
RAW = "https://raw.githubusercontent.com/TimurZak-Zak/embroidery-catalog/main"

DROP = {
    "alcohol-glass-beer-tulip",
    "ten-year-society-publicdomain",
    "36-stanley-hawk-hunting-a-songbird",
}

# slug -> русское имя
RENAME = {
    "floral-border-01-corner-by-paul-b-rck": "Цветочный бордюр 1 — угол",
    "floral-border-01-element-by-paul-b-rck": "Цветочный бордюр 1 — лента",
    "floral-border-02-corner-by-paul-b-rck": "Цветочный бордюр 2 — угол",
    "floral-border-02-element-by-paul-b-rck": "Цветочный бордюр 2 — лента",
    "floral-border-03-corner-by-paul-b-rck": "Цветочный бордюр 3 — угол",
    "floral-border-03-element-by-paul-b-rck": "Цветочный бордюр 3 — лента",
    "floral-border-04-corner-by-paul-b-rck": "Цветочный бордюр 4 — угол",
    "floral-border-04-element-by-paul-b-rck": "Цветочный бордюр 4 — лента",
    "art-nouveau-daisy-headpiece": "Ромашки (модерн)",
    "art-nouveau-floral-ornament-by-e-m-lilien": "Цветочный орнамент (модерн)",
    "art-nouveau-foliage-ornament": "Листва (модерн)",
    "art-nouveau-frond-ornament": "Папоротник (модерн)",
    "art-nouveau-nasturtium-ornament": "Настурция (модерн)",
    "art-nouveau-ornament-01": "Орнамент модерн 1",
    "art-nouveau-ornament-02": "Орнамент модерн 2",
    "art-nouveau-ornament-03": "Орнамент модерн 3",
    "art-nouveau-ornament-04": "Орнамент модерн 4",
    "art-nouveau-title-frame-with-sunflowers": "Рамка с подсолнухами (модерн)",
    "art-nouveau-tulip-ornament": "Тюльпан (модерн)",
    "greek-roman-laurel-wreath-vector": "Лавровый венок",
    "laurel-left": "Лавровая ветвь (левая)",
    "laurel-right": "Лавровая ветвь (правая)",
    "laurelwreath-empty-without-shadow": "Лавровый венок (тонкий)",
    "laurelwreath-empty": "Лавровый венок 2",
    "olive-wreath": "Оливковый венок",
    "steren-laurel": "Лавровый венок 3",
    "greek-roman-laurel-wreath-with-branches-vector": "Лавровый венок с ветвями",
    "laurel-3": "Лавровый венок 4",
    "laurel-wreath-ribbon": "Лавровый венок с лентой",
    "damask": "Дамаск (бордюр)",
    "presquesage-papillon-violet": "Бабочка",
    "yamfly-outline": "Бабочка (контур)",
    "aldus-leaf-unicode2766": "Сердечко-листок",
    "floral-heart": "Цветочное сердце",
    "flower-with-heart-shaped-petals": "Цветок-сердечко",
}


def main():
    cands = json.loads((STAGE / "candidates.json").read_text("utf-8"))
    catalog = json.loads((ROOT / "catalog.json").read_text("utf-8"))
    have = {c["id"] for c in catalog}
    added = 0
    for c in cands:
        slug = c["slug"]
        if slug in DROP:
            continue
        name = RENAME.get(slug)
        if not name:
            print("нет русского имени, пропуск:", slug)
            continue
        shutil.copyfile(STAGE / "designs" / f"{slug}.vp3", ROOT / "designs" / f"{slug}.vp3")
        shutil.copyfile(STAGE / "thumbs" / f"{slug}.png", ROOT / "thumbs" / f"{slug}.png")
        if slug in have:
            continue
        catalog.append({
            "id": slug,
            "name": name,
            "category": c["category"],
            "size_mm": c["size_mm"],
            "thumbnail": f"{RAW}/thumbs/{slug}.png",
            "file_url": f"{RAW}/designs/{slug}.vp3",
            "license": c["license"],
            "author": c.get("author", "Wikimedia Commons"),
            "source": c.get("source", ""),
        })
        have.add(slug)
        added += 1
    (ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), "utf-8"
    )
    print(f"Добавлено: {added}. Всего в каталоге: {len(catalog)}")


if __name__ == "__main__":
    main()
