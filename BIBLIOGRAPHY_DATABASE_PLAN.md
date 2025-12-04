# Bibliography Database Conversion Plan

## Overview

This document outlines the complete plan to convert the HTML bibliography (`primary_recent.html`) into a structured, queryable JSON database for use with the Observable JS interface.

## Current Structure Analysis

### HTML Organization
```
1. Introduction text (with general footnotes 1-5)
2. Collapsible "Continue reading" section
3. "How to use this bibliography" section
4. Legend table (work type color coding)
5. Bibliography organized by:
   - Century (3rd/9th, 4th/10th, 5th/11th)
     - Author (with metadata)
       - Works (with full bibliographic data)
6. Endnotes section (14 footnotes total)
```

### Footnote Types
**General Footnotes (IDs: one, two, three, four, five)**
- Not tied to specific works
- About methodology, project context
- Keep in page content, NOT in database

**Work-Specific Footnotes (IDs: six, seven, eight, nine, ten, eleven, twelve, thirteen, fourteen)**
- Attached to specific works/editions
- Scholarly commentary about attribution, dating, manuscript issues
- **MUST BE CAPTURED** as "scholarlyCommentary" field in database

### Data Structure Per Author
```
- Full name (Arabic transliteration)
- Death date (Hijri/Gregorian)
- Death location (city)
- Century (3rd/9th, 4th/10th, 5th/11th)
- Has multiple works indicator (+)
- Optional: Author-level note (e.g., "bibliography from Gavin Picken")
```

### Data Structure Per Work
```
- Title (Arabic transliteration)
- Title variants (e.g., "Kitāb al-ʿAql or Maʾīyāt / Māhīyāt al-ʿAql")
- Work type: discursive | isnad | reconstruction | uncertain
- Editions[] (array of edition objects)
- Translations[] (array of translation objects)
- Manuscripts[] (array of manuscript references)
- Reproductions[] (array of reproduction references)
- scholarlyCommentary (text from work-specific footnotes)
```

### Edition/Translation Object Structure
```json
{
  "citation": "Full bibliographic citation",
  "link": "URL (optional)",
  "type": "Partial|Complete (default)",
  "language": "English|French|German|etc (for translations)",
  "notes": "Additional notes inline"
}
```

## Database Schema

### Complete JSON Structure
```json
{
  "metadata": {
    "totalAuthors": 32,
    "totalWorks": 149,
    "lastUpdated": "ISO date",
    "version": "1.0",
    "extractedFrom": "primary_recent.html",
    "generalFootnotes": [
      {
        "id": "one",
        "text": "For further information about sources...",
        "backlinkTarget": "p-one"
      }
    ]
  },
  "authors": [
    {
      "id": "burjulani",
      "name": "Abū al-Shaykh Muḥammad b. al-Ḥusayn al-Burjulānī",
      "nameArabic": "",
      "deathDate": "238/852-3",
      "deathLocation": "Baghdad",
      "century": "3rd/9th",
      "hasMultipleWorks": false,
      "authorNote": "",
      "works": [
        {
          "id": "burjulani-1",
          "title": "Kitāb al-Karam wa-l-Jūd wa-Sakhāʾ al-Nufūs",
          "titleVariants": [],
          "titleTranslation": "",
          "type": "isnad",
          "scholarlyCommentary": "",
          "editions": [
            {
              "citation": "ʿĀmir Ḥasan Ṣabrī (ed.). Kitāb al-Karam...",
              "link": "https://drive.google.com/...",
              "type": "complete",
              "notes": ""
            }
          ],
          "translations": [
            {
              "citation": "Bernd Radtke (trans.)...",
              "link": "https://brill.com/...",
              "language": "German",
              "type": "complete",
              "notes": ""
            }
          ],
          "manuscripts": [],
          "reproductions": []
        }
      ]
    }
  ],
  "workSpecificFootnotes": [
    {
      "id": "six",
      "text": "For the view that this work should instead be attributed to...",
      "relatedWorkIds": ["muhasibi-16"],
      "backlinkTarget": "Muḥāsibī-16"
    }
  ]
}
```

## Extraction Roadmap

### Phase 1: Manual Structural Analysis (COMPLETED)
- ✅ Identify HTML structure patterns
- ✅ Map footnote relationships
- ✅ Define database schema
- ✅ Document work type classifications

### Phase 2: Extraction Script Development
**Tools**: Python with BeautifulSoup4 or Node.js with Cheerio

**Script Requirements**:
1. Parse HTML structure
2. Extract author metadata
3. Extract work metadata
4. Parse editions/translations/manuscripts/reproductions
5. Link work-specific footnotes to works
6. Validate extracted data
7. Output JSON

**Key Parsing Challenges**:
- Handle nested collapsible sections (Bootstrap accordion)
- Extract footnote superscript links and match to endnotes
- Parse complex citation formats
- Handle partial editions markers
- Preserve Arabic diacritics and transliteration
- Handle title variants (works with multiple names)

### Phase 3: Data Validation
**Validation Checks**:
- [ ] Verify 32 authors extracted
- [ ] Verify 149 works extracted
- [ ] Verify all 14 footnotes captured
- [ ] Check all footnotes 6-14 linked to correct works
- [ ] Validate all URLs are well-formed
- [ ] Check for missing required fields
- [ ] Verify work type classifications
- [ ] Ensure century groupings correct

### Phase 4: Observable JS Interface Updates

**Required Changes to `primary.qmd`**:

1. **Add footnote display**:
   - Show scholarly commentary below work details
   - Format as callout or expandable section
   - Include backlink to footnote

2. **Enhanced filtering**:
   - Filter by: has scholarly commentary
   - Filter by: language of translations available
   - Filter by: partial vs complete editions

3. **Improved search**:
   - Search in scholarly commentary
   - Search in manuscript locations
   - Search by editor/translator name

4. **Statistics dashboard**:
   - Works by century (bar chart)
   - Works by type (pie chart)
   - Translation languages available
   - Manuscripts by location

### Phase 5: Content Integration

**Update primary.qmd sections**:
1. Keep general footnotes (1-5) in page content
2. Remove legend section (redundant with filters)
3. Keep "How to use" section but update for new interface
4. Add statistics/overview section at top
5. Ensure all 149 works searchable/filterable

## Implementation Timeline

### Immediate (This Session)
1. Create extraction script outline
2. Begin parsing first century (3rd/9th)
3. Validate against known works

### Short-term (Next Session)
1. Complete extraction of all 149 works
2. Validate data completeness
3. Update `data/bibliography.json`
4. Update `primary.qmd` Observable JS code
5. Test interface with full dataset

### Medium-term (Future)
1. Add Arabic text fields
2. Add manuscript images (if available)
3. Create export functionality (BibTeX, CSV, etc.)
4. Add user annotation/notes feature
5. Integrate with secondary scholarship page

## Technical Notes

### Work Type Color Mapping
```
discursive    → btn-light  → #f8f9fa (light gray)
isnad         → btn-info   → #0dcaf0 (cyan/blue)
reconstruction→ btn-warning→ #ffc107 (yellow/amber)
uncertain     → btn-danger → #dc3545 (red)
```

### Footnote ID Mapping Strategy
```
Work-specific footnotes have targets like:
  <sup><a href="#six">6</a></sup>
  Target ID in work: #Muḥāsibī-16
  Footnote content: id="six"

Extraction must preserve this mapping:
  footnoteId: "six"
  relatedWorkIds: ["muhasibi-16"]
```

### Special Cases to Handle
1. **Partial editions**: Mark with `type: "partial"` in citation object
2. **Multiple titles**: Store in `titleVariants` array
3. **Uncertain attributions**: Note in `scholarlyCommentary`
4. **Manuscript fragments**: Include in manuscripts array with fragment notation
5. **Works attributed to multiple authors**: Cross-reference in author notes

## Success Criteria

Database conversion is complete when:
- [ ] All 32 authors represented
- [ ] All 149 works extracted
- [ ] All editions, translations, manuscripts captured
- [ ] All 9 work-specific footnotes (6-14) linked correctly
- [ ] General footnotes (1-5) preserved in page content
- [ ] Observable JS interface functional with full dataset
- [ ] Search returns accurate results
- [ ] Filters work correctly
- [ ] No data loss from original HTML
- [ ] Site successfully deployed to digitalsufism.github.io

## Next Steps

1. **Immediate**: Write Python extraction script
2. **Review**: User approves extraction approach
3. **Execute**: Run extraction on `primary_recent.html`
4. **Validate**: Check completeness and accuracy
5. **Integrate**: Update Quarto site with new data
6. **Deploy**: Push to GitHub and publish

---

**Document Version**: 1.0
**Created**: 2025-12-03
**Author**: Claude Code Assistant
**Status**: Planning Complete, Awaiting Approval
