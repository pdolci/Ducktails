"""Cocktails blueprint: browse, view, and (for admins) manage cocktail recipes.

Endpoints referenced elsewhere (base template):
    cocktails.list, cocktails.detail, cocktails.create, cocktails.edit,
    cocktails.delete, cocktails.toggle_available
"""
from collections import OrderedDict

from flask import flash, redirect, render_template, request, url_for

from app.blueprints.cocktails import bp
from app.blueprints.cocktails.forms import CocktailForm
from app.extensions import db
from app.ingredients import prune_orphan_ingredients, sync_cocktail_ingredients
from app.models import ALL_CATEGORIES, CATEGORY_CUSTOM, Cocktail, Ingredient
from app.utils import admin_required, get_current_user


@bp.route("/")
def list():
    user = get_current_user()
    is_admin = bool(user and user.is_admin)

    query = Cocktail.query

    q = request.args.get("q", "").strip()
    if q:
        query = query.filter(Cocktail.name.ilike(f"%{q}%"))

    category = request.args.get("category", "").strip()
    if category:
        query = query.filter_by(category=category)

    cocktails = query.order_by(Cocktail.name.asc()).all()

    # Customers only see cocktails that are available AND fully in stock.
    # Admins see everything (with badges for hidden / missing-ingredient ones).
    if not is_admin:
        cocktails = [c for c in cocktails if c.is_orderable]

    grouped = OrderedDict((cat, []) for cat in ALL_CATEGORIES)
    for cocktail in cocktails:
        grouped.setdefault(cocktail.category, []).append(cocktail)
    # Drop categories with no results so the template can render a clean layout.
    grouped = OrderedDict((cat, items) for cat, items in grouped.items() if items)

    return render_template(
        "cocktails/list.html",
        grouped=grouped,
        cocktails=cocktails,
        q=q,
        category=category,
        all_categories=ALL_CATEGORIES,
        is_admin=is_admin,
    )


@bp.route("/<int:cocktail_id>")
def detail(cocktail_id):
    cocktail = Cocktail.query.get_or_404(cocktail_id)
    user = get_current_user()
    is_admin = bool(user and user.is_admin)
    return render_template(
        "cocktails/detail.html",
        cocktail=cocktail,
        is_admin=is_admin,
        current_user_present=bool(user),
    )


@bp.route("/new", methods=["GET", "POST"])
@admin_required
def create():
    form = CocktailForm()
    if request.method == "GET":
        form.category.data = CATEGORY_CUSTOM
        form.is_available.data = True

    if form.validate_on_submit():
        name = form.name.data.strip()
        if Cocktail.query.filter_by(name=name).first():
            flash(f'A cocktail named "{name}" already exists.', "danger")
        else:
            cocktail = Cocktail(
                name=name,
                category=form.category.data,
                glass=form.glass.data.strip() if form.glass.data else None,
                ingredients=form.ingredients.data or None,
                garnish=form.garnish.data.strip() if form.garnish.data else None,
                method=form.method.data or None,
                is_iba=False,
                is_available=form.is_available.data,
            )
            db.session.add(cocktail)
            db.session.commit()
            sync_cocktail_ingredients(cocktail)
            prune_orphan_ingredients()
            db.session.commit()
            flash(f'"{cocktail.name}" was created.', "success")
            return redirect(url_for("cocktails.detail", cocktail_id=cocktail.id))

    return render_template("cocktails/form.html", form=form, cocktail=None)


@bp.route("/<int:cocktail_id>/edit", methods=["GET", "POST"])
@admin_required
def edit(cocktail_id):
    cocktail = Cocktail.query.get_or_404(cocktail_id)
    form = CocktailForm(obj=cocktail)

    if form.validate_on_submit():
        name = form.name.data.strip()
        duplicate = Cocktail.query.filter(
            Cocktail.name == name, Cocktail.id != cocktail.id
        ).first()
        if duplicate:
            flash(f'A cocktail named "{name}" already exists.', "danger")
        else:
            cocktail.name = name
            cocktail.category = form.category.data
            cocktail.glass = form.glass.data.strip() if form.glass.data else None
            cocktail.ingredients = form.ingredients.data or None
            cocktail.garnish = form.garnish.data.strip() if form.garnish.data else None
            cocktail.method = form.method.data or None
            cocktail.is_available = form.is_available.data
            db.session.commit()
            sync_cocktail_ingredients(cocktail)
            prune_orphan_ingredients()
            db.session.commit()
            flash(f'"{cocktail.name}" was updated.', "success")
            return redirect(url_for("cocktails.detail", cocktail_id=cocktail.id))

    return render_template("cocktails/form.html", form=form, cocktail=cocktail)


@bp.route("/<int:cocktail_id>/delete", methods=["POST"])
@admin_required
def delete(cocktail_id):
    cocktail = Cocktail.query.get_or_404(cocktail_id)
    name = cocktail.name
    db.session.delete(cocktail)
    db.session.commit()
    prune_orphan_ingredients()
    db.session.commit()
    flash(f'"{name}" was deleted.', "info")
    return redirect(url_for("cocktails.list"))


@bp.route("/<int:cocktail_id>/toggle", methods=["POST"])
@admin_required
def toggle_available(cocktail_id):
    cocktail = Cocktail.query.get_or_404(cocktail_id)
    cocktail.is_available = not cocktail.is_available
    db.session.commit()
    state = "available" if cocktail.is_available else "hidden"
    flash(f'"{cocktail.name}" is now {state}.', "success")
    return redirect(request.referrer or url_for("cocktails.list"))


# --- Bar stock (ingredient inventory) ---------------------------------------

@bp.route("/inventory")
@admin_required
def inventory():
    q = request.args.get("q", "").strip()
    query = Ingredient.query
    if q:
        query = query.filter(Ingredient.name.ilike(f"%{q}%"))
    # Out-of-stock first, then alphabetical.
    ingredients = query.order_by(Ingredient.in_stock.asc(), Ingredient.name.asc()).all()

    out_of_stock_count = Ingredient.query.filter_by(in_stock=False).count()
    hidden = [
        c
        for c in Cocktail.query.filter_by(is_available=True).all()
        if c.missing_ingredients
    ]
    return render_template(
        "cocktails/inventory.html",
        ingredients=ingredients,
        q=q,
        total=Ingredient.query.count(),
        out_of_stock_count=out_of_stock_count,
        hidden_count=len(hidden),
    )


@bp.route("/ingredients/<int:ingredient_id>/toggle", methods=["POST"])
@admin_required
def toggle_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    ingredient.in_stock = not ingredient.in_stock
    db.session.commit()
    state = "in stock" if ingredient.in_stock else "out of stock"
    affected = len([c for c in ingredient.cocktails if c.is_available])
    msg = f'"{ingredient.name}" marked {state}.'
    if not ingredient.in_stock and affected:
        msg += f" {affected} cocktail(s) hidden from customers."
    flash(msg, "success")
    return redirect(request.referrer or url_for("cocktails.inventory"))
