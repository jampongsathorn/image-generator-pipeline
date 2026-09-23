#!/usr/bin/env python3
"""One-off: transcribe the Food4Thought menu audit screenshots into pipeline inputs.

Source: 28 phone screenshots of the restaurant's ordering app (GrabFood-style menu),
marked by the team: green tick = photo is good / keep, red X = photo must be replaced.

Outputs
  inbox/food4thought-2026-09-23/inventory.csv   full audit (every item + mark)
  inbox/food4thought-2026-09-23/requests.csv    pilot round: 10 highest-value redo items

Descriptions are transcribed from the app text where it was readable; truncated text is
marked "…" and the missing part is listed in `confirm_with_kitchen` so the agent never
invents an ingredient on a real menu.
"""

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "inbox" / "food4thought-2026-09-23"
OUT.mkdir(parents=True, exist_ok=True)

# (category, item_name, price, mark, description_seen, confirm_with_kitchen)
# mark: good = green tick (keep) | redo = red X (replace) | redo_na = red X but unavailable
ITEMS = [
    # ---------------- Breakfast sets ----------------
    ("Breakfast Set", "Happy Vegan Breakfast Set", 329, "redo",
     "Vegan eggs, fresh avocado, crispy potatoes, fruit salad, sour-dough toast", "portion of each component; what 'vegan eggs' is made of"),
    ("Breakfast Set", "California Breakfast Set", 379, "redo",
     "1 chorizo sausage link, 2 poached eggs, fresh avocado, quinoa salad, sour-dough toast", "how the eggs are served (shelled/broken), toast count"),
    ("Breakfast Set", "F4T Full English", 389, "redo",
     "Full English breakfast; no black pudding - eggs, bacon, sausage, beans, tomato, mushrooms, toast", "exact components and count of each"),
    ("Breakfast Set", "Country Momma Breakfast Set", 389, "redo",
     "2 pork sausage, 2 made-to-order eggs with cheddar, crispy potatoes, broccoli", "see the current photo"),
    ("Breakfast Set", "Dixie Democrat Breakfast Set", 389, "redo",
     "Smoked ham, 2 made-to-order eggs topped with paprika, fried apples, hash browns", "see the current photo"),
    ("Breakfast Set", "Mediterranean Breakfast set", 389, "redo",
     "2 poached eggs topped with feta, roasted veggies, fresh bruschetta", "bread type, dip selection"),
    ("Breakfast Set", "Daddy Yanky Breakfast Set", 359, "redo_na", "unavailable", "if it returns"),

    # ---------------- Eggs / brunch ----------------
    ("Eggs Brunch", "Bruschetta Toast", 219, "redo",
     "Sourdough toast topped with poached eggs, chopped tomato bruschetta and balsamic glaze", "poached or scrambled"),
    ("Eggs Brunch", "Farmer Omelet", 249, "good",
     "3 eggs, potato, carrot, capsicum, onion, garlic and cheddar, served as a folded omelet", ""),
    ("Eggs Brunch", "Green Omelet", 249, "redo",
     "3 eggs, mushroom, capsicum, zucchini, broccoli and radish, folded omelet", "side items"),
    ("Eggs Brunch", "Garden Medley", 249, "redo",
     "3 eggs poached in a medley of mushrooms, capsicum and zucchini", "container (skillet?), side"),
    ("Eggs Brunch", "Israeli Shashouka", 279, "redo",
     "2 eggs poached in tomato sauce with mushrooms, peppers, olives and garlic", "bread served alongside"),
    ("Eggs Brunch", "Classic Eggs Benedict", 299, "redo",
     "2 poached eggs with smoked ham on toasted bread, glossy hollandaise, side greens and tomato", "side items; bread type"),
    ("Eggs Brunch", "Smoked Ham Avocado Omelet", 299, "redo",
     "Smoked ham, avocado, onion, cherry tomato and cheddar omelet", "side items"),
    ("Eggs Brunch", "Sausage Omelet", 299, "redo",
     "3 eggs, sausage, apple, red onion, kale, feta and sun-dried tomatoes", "side items"),
    ("Eggs Brunch", "Huevos Rancheros", 289, "redo_na", "unavailable", ""),
    ("Eggs Brunch", "Moroccan Eggs", 239, "redo_na", "unavailable", ""),

    # ---------------- Sandwich ----------------
    ("Sandwich", "The Bacon Egg Sandwich", 219, "good",
     "Bacon, egg, cheddar and tomato with chili mayo on a ciabatta roll", ""),
    ("Sandwich", "The Vegan Cheese Steak", 259, "redo",
     "Vegan faux mushroom meat with sweet peppers, onions, garlic and cilantro in a roll", "cheese substitute, garnish"),
    ("Sandwich", "Tuscan Tuna Sandwich", 269, "redo",
     "Tuna bound with lemon, olive, red onion, radish and garlic, ciabatta", "garnish, side"),
    ("Sandwich", "Smoked Ham Sandwich", 279, "redo",
     "Smoked ham with apple, brie and house mustard on ciabatta", "side items"),
    ("Sandwich", "Pesto Sandwich", 279, "redo",
     "Basil pesto with roasted chicken, roasted sweet peppers and mozzarella, toasted", "side items"),
    ("Sandwich", "The Smoked Beef Sandwich", 319, "redo",
     "House smoked beef, mozzarella cheese and roasted capsicum", "side items"),
    ("Sandwich", "Chicken & Brie Sandwich", 259, "redo_na", "unavailable", ""),
    ("Sandwich", "Grilled Cheese", 169, "redo",
     "Cheddar and mozzarella blend grilled between sourdough slices, cut diagonally", "side items"),
    ("Sandwich", "Avocado Egg Sandwich", 199, "redo",
     "Avocado, egg and cheese on ciabatta", "side items"),
    ("Sandwich", "Sun-dried Tomato Toast", 269, "good",
     "Sourdough toast with poached or scrambled eggs, garlic butter and sun-dried tomato", ""),

    # ---------------- Salads ----------------
    ("Salads", "The Deconstructed Spring Roll Salad", 249, "redo",
     "Fried tofu, crispy noodles, peanuts, cucumber, bell pepper and carrot over greens", "dressing"),
    ("Salads", "Avocado Salad", 249, "redo",
     "Avocado-lime dressing with heaps of avocado, fresh fruit and mixed leaves", "fruit used"),
    ("Salads", "Turmeric Chicken Salad", 259, "redo",
     "Chicken salad with raisins, cashew nut, sweet pepper, red onion, scallion and cilantro", ""),
    ("Salads", "Salad Fresh plate", 259, "good",
     "3 small portions of the grain/veggie salad choices", ""),
    ("Salads", "Burmese Tea Leaf Salad", 229, "good",
     "Pickled tea leaves, cucumber, tomato and crispy bits over lettuce", ""),
    ("Salads", "Broccoli Salad", 239, "redo",
     "Broccoli, carrot, radish, parsley, red onion, cranberry and sunflower seeds", ""),
    ("Salads", "Quinoa Salad", 239, "redo",
     "Quinoa, mango, black bean, cashew, raisin, capsicum, red onion and cilantro", ""),
    ("Salads", "Tabouleh Salad", 239, "good",
     "Parsley, mint, barley, cucumber, tomato and radish", ""),
    ("Salads", "Caesar Salad", 299, "redo",
     "Roasted chicken breast, bacon, olives, parmesan, tomato, onion and cucumber over romaine with Caesar dressing", "current photo looks like a scoop; confirm it is sliced chicken"),
    ("Salads", "Asian Cobb", 319, "good",
     "Asian rendering of the classic American salad with chicken and boiled egg", ""),
    ("Salads", "Harvest Salad", 319, "good",
     "Chicken, bacon, pumpkin, apple, dried fruit, nuts and cheddar with balsamic-honey dressing", ""),
    ("Salads", "Citrus Chicken Salad", 249, "redo_na", "unavailable", ""),
    ("Salads", "Warm Kale Salad", 269, "good",
     "Curly kale, brie cheese, slivered almonds and dried cranberries", ""),
    ("Salads", "Mango Quinoa Salad", 269, "redo",
     "Feta cheese, mango, quinoa, avocado and cherry tomato", ""),
    ("Salads", "Protein plate", 289, "good",
     "Roasted chicken with a choice of 2 grain/veggie salads", ""),
    ("Salads", "Curried Chicken Salad", 289, "redo",
     "Mild and sweet curried chicken with dried fruit, nuts, fresh mango and mixed lettuce", ""),
    ("Salads", "Chickpea Salad", 189, "redo",
     "Chickpea, carrot, cabbage, raisin, ginger, sesame, mint and masala", ""),
    ("Salads", "The Burmese Daikon Salad", 199, "good",
     "Pickled daikon radish, red onion, garlic, cilantro, raisin, cashew nut and peanuts", ""),
    ("Salads", "Sweet Potato Salad", 199, "redo",
     "Sweet potato, capsicum, celery, chili, scallion and sesame seeds", ""),
    ("Salads", "Moroccan Carrot Salad", 199, "redo",
     "Carrot, chickpea, almond, raisin, mint and cilantro", ""),

    # ---------------- Pasta ----------------
    ("Pasta", "Rustic Bolognese", 359, "redo",
     "Tomato Bolognese sauce with Italian sausage, onion, carrot and celery over pasta, with garlic bread", ""),
    ("Pasta", "Cajun Fettuccine Pasta", 369, "good",
     "Spicy roasted chili cream with fettuccine, chicken, mushroom, kale, onion and garlic", ""),
    ("Pasta", "Conchiglie & Cheese", 299, "redo",
     "Large shell pasta in a rich cashew cheese sauce", ""),
    ("Pasta", "Spinach & Cheese", 319, "redo",
     "Bacon, spinach, mozzarella cheese, onion and cream", ""),
    ("Pasta", "Butternut Squash Ravioli", 319, "redo",
     "Homemade ravioli filled with roasted butternut squash, tossed in sauce with cherry tomato", "sauce"),
    ("Pasta", "Italian Sausage Ravioli", 319, "good",
     "Ravioli with house Italian sausage (beef and pork), spinach, ricotta and parmesan", ""),
    ("Pasta", "Desert Fire Pasta", 255, "good",
     "Spicy roasted chili cream with fettuccine, chicken, mushroom, kale, onion and garlic", ""),

    # ---------------- Soups ----------------
    ("Soups", "Tomato & Roasted Red Pepper Soup", 229, "redo",
     "Roasted red pepper and tomato soup with cream or coconut milk, served with toast", ""),
    ("Soups", "Butternut Squash Soup", 229, "good",
     "Butternut squash soup with cream or coconut milk, swirl of cream, served with toast", ""),
    ("Soups", "Potato & ham soup", 229, "good",
     "Creamy potato soup with cream, cheese and smoked ham, served with toast", ""),
    ("Soups", "Minnesota Wild-Rice Soup", 239, "redo",
     "Creamy soup with chicken, smoked ham and black rice, served with toast", ""),

    # ---------------- Healthy wraps ----------------
    ("Healthy Wraps", "Falafel Wrap", 239, "redo",
     "House falafel with tabbouleh salad in a tortilla, served with tzatziki, cut diagonally", ""),
    ("Healthy Wraps", "Chicken Cranberry Wrap", 249, "good",
     "Pulled chicken breast, cranberry, almond and romaine with a yogurt-based dressing, in a tortilla", ""),
    ("Healthy Wraps", "Fish and Mango Wrap", 269, "redo",
     "Fried tilapia with mango salsa and a hint of habanero in a tortilla", ""),
    ("Healthy Wraps", "Mexican Wrap", 389, "good",
     "Chicken, black beans, roasted veggies, rice, cheddar and pickled jalapenos in a tortilla", ""),
    ("Healthy Wraps", "Breakfast Wrap", 219, "redo",
     "Eggs, cumin spiced fried potatoes and sour cream wrapped in a tortilla", ""),
    ("Healthy Wraps", "Burmese Wrap", 219, "good",
     "Spicy fermented tea leaf salad rolled in a tortilla, cut diagonally", ""),
    ("Healthy Wraps", "Avocado Wrap", 229, "redo",
     "Avocado, fresh veggies, cheddar cheese and avo-lime dressing in a tortilla", ""),
    ("Healthy Wraps", "Hummus Wrap", 239, "redo",
     "Roasted eggplant, zucchini, capsicum and carrot with hummus in a tortilla, hummus pot on the side", ""),

    # ---------------- Burger / bagel ----------------
    ("Burger / Bagel", "Mushroom Burger", 279, "redo",
     "Shiitake mushroom patty with vegan cheese, yellow mustard and ketchup in a seeded bun, with fries", ""),
    ("Burger / Bagel", "Chicken Grapow Burger", 269, "redo",
     "Spicy chicken patty with a fried egg, cheddar cheese and crispy fried basil in a bun", ""),
    ("Burger / Bagel", "The Pulled Pork Burger", 279, "redo",
     "House-made smoked pulled pork with house BBQ sauce and cheddar in a bun", ""),
    ("Burger / Bagel", "Black & Blue Burger", 329, "good",
     "Chuck and brisket patty with bleu cheese, bacon and roasted chilli-mango in a bun", ""),
    ("Burger / Bagel", "Roasted Chicken Burger", 215, "good",
     "Grilled chicken breast with roquette, fresh tomato, sun-dried tomato and mozzarella in a bun", ""),
    ("Burger / Bagel", "Tomato Basil Bagel", 199, "redo_na", "unavailable", ""),
    ("Burger / Bagel", "Cucumber Mint Bagel", 199, "redo_na", "unavailable", ""),
    ("Burger / Bagel", "PB & J Bagel", 199, "redo_na", "unavailable", ""),
    ("Burger / Bagel", "Duck Burger", 289, "redo_na", "unavailable", ""),

    # ---------------- Waffles / oats ----------------
    ("Waffles / Oats", "Sausage & Waffles", 289, "redo",
     "Waffle with two house pork sausages, mango and orange slices", ""),
    ("Waffles / Oats", "Chicken & Waffle", 329, "redo",
     "Waffle with chicken in a sweet and spicy sauce and a whipped orange infusion", ""),
    ("Waffles / Oats", "Cajun Shrimp & Grits", 349, "good",
     "Corn porridge (grits) with cajun shrimp and herb garnish", ""),
    ("Waffles / Oats", "Swedish Pancakes", 249, "redo",
     "Thin folded pancakes topped with berry sauce, cream and fresh mint", ""),
    ("Waffles / Oats", "Oats Porridge", 229, "redo",
     "Oat porridge with milk, masala chai or coconut milk, topped with fruit and seeds", ""),
    ("Waffles / Oats", "Chia Pudding", 229, "redo",
     "Chia seed and coconut milk pudding with mixed fresh fruit and dried fruit", ""),
    ("Waffles / Oats", "Muesli", 229, "redo",
     "Muesli topped with mixed fresh fruits, dried fruit and nuts", ""),
    ("Waffles / Oats", "Buttermilk Pancakes", 229, "redo",
     "Short stack of buttermilk pancakes with butter, banana and maple syrup", "toppings"),
    ("Waffles / Oats", "French Toast", 249, "redo",
     "Sourdough French toast in custard with butter and sour cream, fruit on the side", ""),
    ("Waffles / Oats", "Sweet potato & Quinoa Waffle", 249, "redo",
     "Waffle filled with sweet potato, quinoa, rice and curly kale, topped with cream and sliced fruit", ""),
    ("Waffles / Oats", "Savory Waffle", 289, "redo",
     "Waffle with fried egg, bacon, mango chutney, brie, parmesan and sour cream", ""),

    # ---------------- Snacks ----------------
    ("Snacks Shareable", "Tilapia Ceviche", 269, "redo",
     "Marinated raw tilapia with a Thai twist, chopped herbs and lime, served with crackers", ""),
    ("Snacks Shareable", "Chicken Nachos", 279, "good",
     "Tortilla chips with chicken, black beans, roasted veggies, cheddar and fresh onion, salsa on the side", ""),
    ("Snacks Shareable", "Chicken Quesadillas", 279, "good",
     "Grilled quesadilla with chicken, tomato, onion and cilantro, mozzarella and sour cream", ""),
    ("Snacks Shareable", "Black Bean Quesadilla", 279, "redo",
     "Quesadilla with black beans, fresh tomato, onion, cilantro and mozzarella", ""),
    ("Snacks Shareable", "Carnitas Tacos", 279, "redo",
     "3 tortillas with spicy smoky carnitas pork, fresh pineapple, parmesan and crema", ""),
    ("Snacks Shareable", "Fish Tacos", 289, "redo",
     "3 tortillas with fried fish and cabbage, guacamole and spicy sauce", ""),
    ("Snacks Shareable", "Chicken Wings", 219, "redo_na", "unavailable", ""),
    ("Snacks Shareable", "Avocado Fries", 129, "redo",
     "Avocado wedges in panko, fried golden, served with garlic aioli", ""),
    ("Snacks Shareable", "Fresh Cut Veggies & Dip", 199, "redo",
     "Fresh cut vegetables with red-pepper hummus and garlic hummus, toasted bread", ""),
    ("Snacks Shareable", "Chip & Salsa", 219, "redo",
     "House tortilla chips with salsa and guacamole", ""),
    ("Snacks Shareable", "Black Bean Dip", 259, "good",
     "Warm black bean puree topped with mozzarella, served with tortilla chips", ""),
]

INVENTORY_COLUMNS = ["id", "category", "item_name", "price_thb", "mark", "description_seen", "confirm_with_kitchen"]


def slug(name: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in name]
    return "-".join("".join(keep).split("-")).strip("-")[:40] or "item"


def main() -> None:
    rows = []
    for i, (category, name, price, mark, desc, confirm) in enumerate(ITEMS, start=1):
        rows.append({
            "id": f"F4T-{i:03d}",
            "category": category,
            "item_name": name,
            "price_thb": price,
            "mark": mark,
            "description_seen": desc,
            "confirm_with_kitchen": confirm,
        })
    with (OUT / "inventory.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=INVENTORY_COLUMNS)
        w.writeheader()
        w.writerows(rows)

    redo = [r for r in rows if r["mark"] == "redo"]
    redo_na = [r for r in rows if r["mark"] == "redo_na"]
    good = [r for r in rows if r["mark"] == "good"]
    print(f"inventory : {len(rows)} items")
    print(f"  keep (green) : {len(good)}")
    print(f"  redo (red)   : {len(redo)}   <- available now, needs a photo")
    print(f"  redo but unavailable : {len(redo_na)}")
    print(f"  rounds needed at 10/round: {-(-len(redo) // 10)}")

    # ---- pilot round: 10 highest-value redo items across categories ----
    pilot_ids = [
        "F4T-013",  # Classic Eggs Benedict    (signature dish, promo price)
        "F4T-066",  # Hummus Wrap              (signature dish, promo price)
        "F4T-079",  # Swedish Pancakes         (signature dish)
        "F4T-036",  # Caesar Salad             (current photo looks wrong)
        "F4T-002",  # California Breakfast Set
        "F4T-003",  # F4T Full English
        "F4T-067",  # Mushroom Burger          (vegan flagship)
        "F4T-091",  # Carnitas Tacos
        "F4T-025",  # Grilled Cheese           (cheap entry item, high volume)
        "F4T-094",  # Avocado Fries
    ]
    by_id = {r["id"]: r for r in rows}
    sheet = OUT / "requests.csv"
    columns = ["id", "item_name", "use_case", "description", "ref_images", "aspect", "delivery_px",
               "format", "text_verbatim", "must_keep", "must_avoid", "asset_type", "priority", "notes"]
    with sheet.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        for rank, rid in enumerate(pilot_ids, start=1):
            item = by_id[rid]
            notes = "pilot round 1"
            if item["confirm_with_kitchen"]:
                notes += f"; confirm with kitchen: {item['confirm_with_kitchen']}"
            w.writerow({
                "id": item["id"],
                "item_name": item["item_name"],
                "use_case": "food-hero",
                "description": item["description_seen"],
                "ref_images": "",
                "aspect": "1:1",
                "delivery_px": "2048",
                "format": "jpeg",
                "text_verbatim": "",
                "must_keep": "the dish exactly as the kitchen serves it (ingredients, portion, plating)",
                "must_avoid": "ingredients that are not in the description; extra sides; restaurant logo or text",
                "asset_type": f"menu photo - {item['category']}",
                "priority": "high" if rank <= 6 else "medium",
                "notes": notes,
            })
    print(f"pilot sheet: {sheet} ({len(pilot_ids)} rows)")


if __name__ == "__main__":
    main()
