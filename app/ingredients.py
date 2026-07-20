"""Bar-stock ingredient index.

Recipe ingredients are stored as free text (one line per ingredient, e.g.
"30 ml Campari"). To let admins toggle stock at the ingredient level, we parse
those lines into canonical ingredient names and keep a Cocktail<->Ingredient
link table in sync. When an ingredient is marked out of stock, every cocktail
that needs it becomes non-orderable (see Cocktail.is_orderable).
"""
import re

from app.extensions import db
from app.models import Cocktail, Ingredient

# Quantity/measure words stripped when extracting the ingredient name.
_UNITS = {
    "ml", "cl", "l", "oz", "cts", "ct", "part", "parts", "dash", "dashes",
    "drop", "drops", "tsp", "tspn", "teaspoon", "teaspoons", "tbsp",
    "tablespoon", "tablespoons", "barspoon", "barspoons", "spoon", "spoons",
    "cube", "cubes", "splash", "splashes", "slice", "slices", "sprig", "sprigs",
    "leaf", "leaves", "wedge", "wedges", "piece", "pieces", "twist", "twists",
    "shot", "shots", "glass", "cup", "cups", "scoop", "scoops", "bar", "fresh",
    "whole", "chilled", "cold",
}
_FILLER = {"of", "a", "an", "the"}
_TRAILING_PHRASES = [
    " to top", " to fill", " to taste", " for garnish", " to rinse",
    " cut in wedges", " cut into wedges", " cut in wheels", " to float",
]
_QTY = re.compile(r"^[\d]+(?:[.,/\-–—][\d]+)?$")


def parse_ingredient_name(line):
    """Extract a canonical ingredient name from one recipe line, or None."""
    s = (line or "").strip()
    if not s:
        return None
    # Drop parenthetical notes, e.g. "Apple Brandy (Calvados)" -> "Apple Brandy".
    s = re.sub(r"\([^)]*\)", "", s)
    s = s.replace("(", " ").replace(")", " ").strip()
    if not s:
        return None
    low = s.lower()
    for tail in _TRAILING_PHRASES:
        idx = low.find(tail)
        if idx != -1:
            s = s[:idx]
            low = s.lower()

    tokens = [t for t in re.split(r"\s+", s) if t]

    def is_noise(tok):
        t = tok.lower().strip(".,()")
        return (not t) or _QTY.match(t) or t in _UNITS or t in _FILLER

    start = 0
    while start < len(tokens) and is_noise(tokens[start]):
        start += 1
    end = len(tokens)
    while end > start and is_noise(tokens[end - 1]):
        end -= 1

    name = " ".join(tokens[start:end]).strip(" ,.-()")
    if len(name) < 2:
        return None
    return re.sub(r"\s+", " ", name).strip().title()


def get_or_create_ingredient(name):
    key = name.casefold()
    existing = Ingredient.query.filter(db.func.lower(Ingredient.name) == key).first()
    if existing:
        return existing
    ing = Ingredient(name=name, in_stock=False)
    db.session.add(ing)
    db.session.flush()  # so later lookups in the same pass find it
    return ing


def sync_cocktail_ingredients(cocktail):
    """(Re)build the ingredient links for one cocktail from its recipe text."""
    seen = set()
    linked = []
    for line in (cocktail.ingredients or "").splitlines():
        name = parse_ingredient_name(line)
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        linked.append(get_or_create_ingredient(name))
    cocktail.required_ingredients = linked


def prune_orphan_ingredients():
    """Delete ingredients no longer referenced by any cocktail."""
    for orphan in Ingredient.query.filter(~Ingredient.cocktails.any()).all():
        db.session.delete(orphan)


def rebuild_ingredient_index():
    """Rebuild ingredient links for every cocktail (idempotent)."""
    for cocktail in Cocktail.query.all():
        sync_cocktail_ingredients(cocktail)
    prune_orphan_ingredients()
    db.session.commit()
