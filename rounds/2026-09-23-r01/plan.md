# Prompt plan - 2026-09-23-r01

- brand/campaign: **Food4Thought** - Menu photo refresh 2026 (62 items)
- source sheet: `/tmp/pilot.csv`
- items: **10** (generate at most 10 per round)

## 1. `F4T-013` - Classic Eggs Benedict
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-013__classic-eggs-benedict.png`  ->  final: `out/f4t-013__classic-eggs-benedict.jpg`
- priority: high  |  notes: pilot round 1; confirm with kitchen: side items; bread type
- **QA**: prompt is 1643 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Eggs Brunch
Primary request: 2 poached eggs with smoked ham on toasted bread, glossy hollandaise, side greens and tomato
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Classic Eggs Benedict - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 2. `F4T-066` - Hummus Wrap
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-066__hummus-wrap.png`  ->  final: `out/f4t-066__hummus-wrap.jpg`
- priority: high  |  notes: pilot round 1
- **QA**: prompt is 1641 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Healthy Wraps
Primary request: Roasted eggplant, zucchini, capsicum and carrot with hummus in a tortilla, hummus pot on the side
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Hummus Wrap - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 3. `F4T-079` - Swedish Pancakes
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-079__swedish-pancakes.png`  ->  final: `out/f4t-079__swedish-pancakes.jpg`
- priority: high  |  notes: pilot round 1
- **QA**: prompt is 1616 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Waffles / Oats
Primary request: Thin folded pancakes topped with berry sauce, cream and fresh mint
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Swedish Pancakes - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 4. `F4T-036` - Caesar Salad
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-036__caesar-salad.png`  ->  final: `out/f4t-036__caesar-salad.jpg`
- priority: high  |  notes: pilot round 1; confirm with kitchen: current photo looks like a scoop; confirm it is sliced chicken
- **QA**: prompt is 1647 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Salads
Primary request: Roasted chicken breast, bacon, olives, parmesan, tomato, onion and cucumber over romaine with Caesar dressing
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Caesar Salad - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 5. `F4T-002` - California Breakfast Set
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-002__california-breakfast-set.png`  ->  final: `out/f4t-002__california-breakfast-set.jpg`
- priority: high  |  notes: pilot round 1; confirm with kitchen: how the eggs are served (shelled/broken), toast count
- **QA**: prompt is 1642 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Breakfast Set
Primary request: 1 chorizo sausage link, 2 poached eggs, fresh avocado, quinoa salad, sour-dough toast
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: California Breakfast Set - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 6. `F4T-003` - F4T Full English
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-003__f4t-full-english.png`  ->  final: `out/f4t-003__f4t-full-english.jpg`
- priority: high  |  notes: pilot round 1; confirm with kitchen: exact components and count of each
- **QA**: prompt is 1645 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Breakfast Set
Primary request: Full English breakfast; no black pudding - eggs, bacon, sausage, beans, tomato, mushrooms, toast
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: F4T Full English - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 7. `F4T-067` - Mushroom Burger
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-067__mushroom-burger.png`  ->  final: `out/f4t-067__mushroom-burger.jpg`
- priority: medium  |  notes: pilot round 1
- **QA**: prompt is 1646 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Burger / Bagel
Primary request: Shiitake mushroom patty with vegan cheese, yellow mustard and ketchup in a seeded bun, with fries
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Mushroom Burger - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 8. `F4T-091` - Carnitas Tacos
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-091__carnitas-tacos.png`  ->  final: `out/f4t-091__carnitas-tacos.jpg`
- priority: medium  |  notes: pilot round 1
- **QA**: prompt is 1629 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Snacks Shareable
Primary request: 3 tortillas with spicy smoky carnitas pork, fresh pineapple, parmesan and crema
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Carnitas Tacos - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 9. `F4T-025` - Grilled Cheese
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-025__grilled-cheese.png`  ->  final: `out/f4t-025__grilled-cheese.jpg`
- priority: medium  |  notes: pilot round 1; confirm with kitchen: side items
- **QA**: prompt is 1619 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Sandwich
Primary request: Cheddar and mozzarella blend grilled between sourdough slices, cut diagonally
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Grilled Cheese - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

## 10. `F4T-094` - Avocado Fries
- use case: `food-hero`  |  aspect: 1:1  |  delivery: 2048px jpeg
- raw: `raw/f4t-094__avocado-fries.png`  ->  final: `out/f4t-094__avocado-fries.jpg`
- priority: medium  |  notes: pilot round 1
- **QA**: prompt is 1612 chars - trim the description, long prompts dilute the important parts

```text
Use case: food-hero
Asset type: menu photo - Snacks Shareable
Primary request: Avocado wedges in panko, fried golden, served with garlic aioli
Scene/backdrop: plain white or light-wood table, clean neutral background, no props beyond the dish and its own sides
Subject: Avocado Fries - the food or drink exactly as described, with the correct portion, container and garnish
Style/medium: natural daylight food photography, honest home-kitchen plating
Composition/framing: square 1:1 format
Lighting/mood: soft daylight from the side-left with gentle fill, natural shadows
Mood: honest, fresh, home-kitchen made - appetizing without looking staged
Color palette: fresh natural colours, plenty of green and red accents on white crockery, light wood and white surfaces
Materials/textures: real food texture: crumb and crust, glossy sauce, fresh herbs, natural moisture
Constraints: the dish exactly as the kitchen serves it (ingredients, portion, plating); fresh and appetizing at first glance; correct portion and garnish exactly as described; visible food texture (crumb, crust, glossy sauce, fresh herbs); steam only on hot dishes; photographic realism with one consistent light direction; colour, shape and proportions true to the reference image
Avoid: ingredients that are not in the description; extra sides; restaurant logo or text; wilted, dry or plastic-looking food; fake or misplaced garnish; cluttered props; messy spills; watermark or caption bar; misspelled, invented or unapproved text or claims; unapproved health, nutrition or certification claims; HDR look, heavy vignette or oversaturated colour
```

---
Generated by `tools/igp.py plan`. If data entry mis-specified something, fix the prompt lines here and pass the corrected text straight to the image tool.
