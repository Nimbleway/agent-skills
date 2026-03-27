# Page Discovery Patterns

How to identify provider/practitioner pages on healthcare practice websites.

## URL Path Patterns (scored by likelihood)

### High confidence (score 10)
```
/providers
/our-providers
/our-doctors
/doctors
/physicians
/meet-our-doctors
/meet-the-team
/our-physicians
/provider-directory
/find-a-doctor
/find-a-provider
```

### Medium confidence (score 7)
```
/team
/our-team
/about/team
/about-us/our-team
/staff
/our-staff
/people
/specialists
/clinicians
/about/providers
```

### Individual practitioner pages (score 8)
```
/dr-{name}
/doctor-{name}
/providers/{name}
/doctors/{name}
/team/{name}
/staff/{name}
/{first}-{last}-md
/{first}-{last}-do
/{first}-{last}-od
```

### Specialty pages with practitioner listings (score 5)
```
/retina
/glaucoma
/cataract
/cornea
/lasik
/services/{specialty}  (often lists the specialist)
/departments/{specialty}
```

### Location pages (score 3, check for embedded provider lists)
```
/locations
/locations/{office-name}
/offices
/contact
```

## Content Signals (for pages where URL isn't conclusive)

After extraction, check the page content for these signals:

### Strong practitioner signals
- Multiple instances of credential patterns (MD, DO, OD, FACS)
- Repeating card/grid layout with headshots
- "Meet our" + "doctors|providers|physicians|team"
- Names followed by comma + credentials (e.g., "John Smith, MD")
- Links containing `/dr-` or `/provider/`

### Weak signals (need 2+ to qualify)
- "Board certified"
- "Fellowship trained"
- "Accepting new patients"
- Headshot images with alt text containing names
- Structured data markup (`schema.org/Physician`)

## Site Structure Heuristics

### Common CMS patterns

**ModMed / EMA:**
- Provider pages at `/providers` or `/team`
- Individual pages at `/providers/{slug}`
- Often has structured JSON-LD for each provider

**Wordpress (most common):**
- Varies widely; look for `/team`, `/staff`, custom post types
- Plugins like "Team Members" use `/team-member/{name}`

**Squarespace:**
- `/team` or custom pages
- Individual bios often on the same page (single-page layout)

**Custom / Enterprise:**
- Often `/find-a-doctor` with search interface
- May use JavaScript rendering — need `--render` flag

## Multi-Location Practices

Large practices (10+ locations) often have:
- A master provider directory at `/providers` or `/find-a-doctor`
- Per-location pages at `/locations/{city}` with local providers listed
- Both should be extracted; deduplicate practitioners by name + credentials

## Handling Edge Cases

- **PDF provider directories:** Log as "PDF detected, manual review needed"
- **Image-only team pages:** Log as "image-based, manual review needed"
- **Login-gated directories:** Skip, log as "requires authentication"
- **Iframe-embedded:** Try extracting the iframe source URL directly
- **Pagination:** If provider list has page 1/2/3 links, extract all pages
