# Query Strategies

Pre-built search query lists by category, plus the formula for generating custom queries.

## Query Generation Formula

For any category, generate 10+ queries following this pattern:

1. **Direct category terms** (3-4 queries): `"{place_type} in {neighborhood}"`, `"{synonym} {neighborhood}"`, `"best {place_type} {neighborhood}"`
2. **Subcategory terms** (3-4 queries): Specific subtypes within the category
3. **Quality/specialty terms** (2-3 queries): Terms that signal higher quality
4. **Adjacent/overlap terms** (2-3 queries): Related categories that may surface the same places

## Pre-Built Query Lists

### Coffee

```
coffee shop {neighborhood}
cafe {neighborhood}
espresso bar {neighborhood}
specialty coffee {neighborhood}
third wave coffee {neighborhood}
coffee roaster {neighborhood}
best coffee {neighborhood}
pour over coffee {neighborhood}
latte art {neighborhood}
coffee house {neighborhood}
matcha cafe {neighborhood}
```

### Restaurant

```
restaurant {neighborhood}
dining {neighborhood}
best restaurant {neighborhood}
fine dining {neighborhood}
casual dining {neighborhood}
brunch {neighborhood}
dinner {neighborhood}
bistro {neighborhood}
eatery {neighborhood}
new restaurant {neighborhood}
restaurant bar {neighborhood}
```

### Bar

```
bar {neighborhood}
cocktail bar {neighborhood}
wine bar {neighborhood}
dive bar {neighborhood}
craft beer {neighborhood}
brewery {neighborhood}
pub {neighborhood}
speakeasy {neighborhood}
best bar {neighborhood}
happy hour {neighborhood}
rooftop bar {neighborhood}
```

### Gym / Fitness

```
gym {neighborhood}
fitness {neighborhood}
crossfit {neighborhood}
yoga studio {neighborhood}
pilates {neighborhood}
personal training {neighborhood}
boxing gym {neighborhood}
climbing gym {neighborhood}
spin class {neighborhood}
martial arts {neighborhood}
fitness studio {neighborhood}
```

### Bakery

```
bakery {neighborhood}
pastry shop {neighborhood}
bread bakery {neighborhood}
patisserie {neighborhood}
sourdough {neighborhood}
croissant {neighborhood}
cake shop {neighborhood}
best bakery {neighborhood}
artisan bakery {neighborhood}
viennoiserie {neighborhood}
```

## Zone Coverage Strategy

### Generating Zones

1. Find the neighborhood center using `nimble search --query "{neighborhood} {city}" --focus geo --max-results 3 --search-depth lite`
2. Tile outward at zoom level 15 (~1km x 1km per tile)
3. Use ~30% overlap between zones to catch boundary places
4. Typical coverage: 4 zones (small neighborhood) to 8 zones (large area)

### Zone Layout Example (6 zones for medium neighborhood)

```
    [Z1] [Z2]
  [Z3] [Z4] [Z5]
    [Z6]
```

Each zone is defined by a center lat/lng at zoom 15.

### Text-Geo Fallbacks

For each query, also run a text-only version (no coordinates):
```
"{query}" in {neighborhood}, {city}
```

This catches places that Google Maps doesn't surface in coordinate-based search
but does return for text queries.
