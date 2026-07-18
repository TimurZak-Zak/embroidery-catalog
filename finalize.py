"""Переносит выбранные staging-кандидаты в живой каталог с русскими именами."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "staging"
RAW = "https://raw.githubusercontent.com/TimurZak-Zak/embroidery-catalog/main"

# slug -> (русское имя, категория)
KEEP = {
    "abstract-floral-ornament": ("Цветочный орнамент", "Цветы"),
    "acorn-square-ornament-purple": ("Орнамент с жёлудем", "Узоры"),
    "art-nouveau-floral-ornament-by-e-m-lilien": ("Цветочный модерн", "Цветы"),
    "everybody-s-floral-ornament": ("Цветочный узор", "Цветы"),
    "flowerc-ornament-black": ("Цветок", "Цветы"),
    "flower-ornament-coloured": ("Ромашка", "Цветы"),
    "flower-in-pot-ornament-green": ("Цветок в вазоне", "Цветы"),
    "flower-in-ring-ornament-red": ("Цветок в круге", "Цветы"),
    "flower-in-ring-ornament-red-r": ("Цветок в круге 2", "Цветы"),
    "secessionistische-zeitung-floral-ornament-1899": ("Вертикальный узор", "Узоры"),
    "crow-standing-with-red-key": ("Ворон с ключом", "Птицы"),
    "crow-standing-with-red-key-2": ("Ворон с ключом 2", "Птицы"),
    "hibiskus": ("Гибискус", "Цветы"),
}


def main():
    cands = {c["slug"]: c for c in json.loads((STAGE / "candidates.json").read_text("utf-8"))}
    catalog = json.loads((ROOT / "catalog.json").read_text("utf-8"))
    have = {c["id"] for c in catalog}
    added = 0
    for slug, (name, category) in KEEP.items():
        c = cands.get(slug)
        if not c:
            print("нет кандидата:", slug)
            continue
        shutil.copyfile(STAGE / "designs" / f"{slug}.vp3", ROOT / "designs" / f"{slug}.vp3")
        shutil.copyfile(STAGE / "thumbs" / f"{slug}.png", ROOT / "thumbs" / f"{slug}.png")
        if slug in have:
            continue
        catalog.append({
            "id": slug,
            "name": name,
            "category": category,
            "size_mm": c["size_mm"],
            "thumbnail": f"{RAW}/thumbs/{slug}.png",
            "file_url": f"{RAW}/designs/{slug}.vp3",
            "license": c["license"],
            "author": c.get("author", "Wikimedia Commons"),
            "source": c.get("source", ""),
        })
        have.add(slug)
        added += 1
        print(f"[+] {name}  ({slug})")
    (ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), "utf-8"
    )
    print(f"Добавлено: {added}. Всего в каталоге: {len(catalog)}")


if __name__ == "__main__":
    main()
