# Vertical-Specific Queries

Search query templates by healthcare vertical. Each set is designed to maximize
coverage while minimizing false positives.

## Query Design Principles

1. **Use specific professional terms** — "ophthalmologist" > "eye doctor" for precision
2. **Include subspecialties** — catches specialist-only practices that generic terms miss
3. **Include practice format terms** — "center", "clinic", "associates", "group"
4. **Avoid overly broad terms** — "vision" alone returns opticians, frame shops, etc.

## Ophthalmology

```python
OPHTHALMOLOGY_QUERIES = [
    "ophthalmology practice {metro}",
    "ophthalmologist {metro}",
    "eye doctor ophthalmology {metro}",
    "retina specialist {metro}",
    "cataract surgeon {metro}",
    "LASIK center {metro}",
    "glaucoma specialist {metro}",
    "eye surgery center {metro}",
    "ophthalmology associates {metro}",
    "cornea specialist {metro}",
    "oculoplastic surgeon {metro}",
    "pediatric ophthalmologist {metro}",
]
```

**False positive filters:** Exclude results with primary category matching:
- "Optician", "Eyewear", "Optical Shop", "Contact Lens"
- Keep "Optometrist" only if practice also lists ophthalmology services

## Dental

```python
DENTAL_QUERIES = [
    "dental practice {metro}",
    "dentist {metro}",
    "dental office {metro}",
    "family dentist {metro}",
    "cosmetic dentist {metro}",
    "oral surgeon {metro}",
    "orthodontist {metro}",
    "periodontist {metro}",
    "endodontist {metro}",
    "pediatric dentist {metro}",
    "dental implants {metro}",
    "dental group {metro}",
]
```

## Dermatology

```python
DERMATOLOGY_QUERIES = [
    "dermatology practice {metro}",
    "dermatologist {metro}",
    "skin doctor {metro}",
    "dermatology clinic {metro}",
    "cosmetic dermatology {metro}",
    "Mohs surgery {metro}",
    "skin cancer specialist {metro}",
    "dermatology associates {metro}",
    "medical dermatology {metro}",
    "pediatric dermatologist {metro}",
]
```

## Orthopedics

```python
ORTHOPEDICS_QUERIES = [
    "orthopedic practice {metro}",
    "orthopedic surgeon {metro}",
    "orthopedics {metro}",
    "sports medicine {metro}",
    "joint replacement {metro}",
    "spine surgeon {metro}",
    "hand surgeon {metro}",
    "orthopedic associates {metro}",
    "foot ankle specialist {metro}",
    "shoulder knee specialist {metro}",
]
```

## Primary Care / Family Medicine

```python
PRIMARY_CARE_QUERIES = [
    "primary care practice {metro}",
    "family medicine {metro}",
    "family doctor {metro}",
    "internal medicine {metro}",
    "general practitioner {metro}",
    "family practice {metro}",
    "primary care physician {metro}",
    "concierge medicine {metro}",
]
```

## Cardiology

```python
CARDIOLOGY_QUERIES = [
    "cardiology practice {metro}",
    "cardiologist {metro}",
    "heart doctor {metro}",
    "cardiovascular {metro}",
    "interventional cardiology {metro}",
    "electrophysiologist {metro}",
    "cardiac surgery {metro}",
    "cardiology associates {metro}",
]
```

## Urology

```python
UROLOGY_QUERIES = [
    "urology practice {metro}",
    "urologist {metro}",
    "urology clinic {metro}",
    "urology associates {metro}",
    "men's health urology {metro}",
    "urologic surgeon {metro}",
]
```

## Generic (any vertical)

For verticals not listed above, generate queries using this template:

```python
def generate_queries(specialty: str) -> list[str]:
    return [
        f"{specialty} practice {{metro}}",
        f"{specialty} doctor {{metro}}",
        f"{specialty} clinic {{metro}}",
        f"{specialty} specialist {{metro}}",
        f"{specialty} center {{metro}}",
        f"{specialty} associates {{metro}}",
        f"{specialty} group {{metro}}",
        f"best {specialty} {{metro}}",
    ]
```

## Query Count by Tier

| Metro tier | Queries to run | Rationale |
|------------|---------------|-----------|
| Tier 1 (top 50) | All 10-12 | Maximum coverage for largest markets |
| Tier 2 (51-150) | Top 5 | Good coverage, balanced cost |
| Tier 3 (151-390) | Top 3 | Broad terms only; specialist queries rarely match |
| Tier 4 (rural) | Top 2 | Just specialty + "doctor" terms |
