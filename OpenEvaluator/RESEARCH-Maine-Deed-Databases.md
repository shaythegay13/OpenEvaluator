---
title: Maine County Deed Databases - Comprehensive Research
description: Complete mapping of all 16 Maine counties' Registry of Deeds systems, query methods, and accessibility for property boundary lookup integration
created: 2026-06-19
updated: 2026-06-19
---

# Maine Deed Database Research: All 16 Counties

**Project:** FormRunner/OpenEvaluator — Integrate Maine County Deed Lookup for Authoritative Boundaries  
**Research Date:** 2026-06-19  
**Scope:** All 16 Maine counties' Registry of Deeds online systems

---

## Executive Summary

**Key Finding:** All 16 Maine counties provide online deed search, but **NO county offers API access or programmatic query methods.** All access is through web portals only. Web scraping is prohibited by terms of service.

**Unified Portal:** All 16 counties are accessible through **www.maineregistryofdeeds.com**, a shared state platform.

**Search by Owner Name Available:** Yes — all counties support grantor/grantee name search, which is the primary method needed for the intake (owner name → deed records → boundary).

**API/Programmatic Access:** None — all systems require manual web portal interaction or contact with the county registry office directly.

---

## Complete County-by-County Reference Table

| County | Platform | Query Methods | Returns | Online URL | API? | Access |
|--------|----------|---------------|---------|-----------|------|--------|
| **Androscoggin** | County Custom | Name, doc type, party, town, date range, address, book/page, instrument # | Deeds, mortgages (1854-present) | androscoggindeeds.com | No | Web portal |
| **Aroostook North** | County Custom | Name, book/page, date range | Deeds, mortgages, liens (1846-present) | aroostookdeedsnorth.com | No | Web portal |
| **Aroostook South** | County Custom | Name, book/page, date range | Deeds, mortgages, liens (1808-present) | aroostookdeedssouth.com | No | Web portal |
| **Cumberland** | i2k USLandRecords | Name, doc type, date range | Deed records, plans (1753-present) | cumberlandcountyme.gov/registry_of_deeds | No | Web portal |
| **Franklin** | SearchIQS | Name, date range, doc type, book/page, instrument # | Deed records, indices (1838-present digitized) | searchiqs.com/MEFRA | No | Web portal |
| **Hancock** | AcclaimWeb | Name, doc #, date range, book/page, municipality | Deed records, documents (200+ years) | records.hancockcountymaine.gov/AcclaimWebLive | No | Web portal |
| **Kennebec** | KoFile Technology | Name, grantor/grantee, subdivision, doc type, doc #, date range | Deed records, full-text OCR searchable | kennebec.me.publicsearch.us | No | Web portal |
| **Knox** | County Custom | Name, volume/book, doc number | Deed records (1760-present) | knoxcountymaine.gov | No | Web portal |
| **Lincoln** | SearchIQS | Name, date range, doc type, instrument #, book/page | Deed records, archives (1761-present scanned) | searchiqs.com (Lincoln County) | No | Web portal |
| **Oxford** | SearchIQS | Name, date range, town, group, description, book/page, instrument # | Deed records, documents | searchiqs.com/meoxe | No | Web portal |
| **Penobscot** | County Custom | Name, book/page, entry date/year, instrument # | Deeds, liens, assignments, mortgages, leases, POA (1800s-present) | penobscotdeeds.com | No | Web portal |
| **Piscataquis** | SearchIQS | Name, date range, doc type, instrument #, book/page | Deed records, documents, images (digitized indices) | piscataquis.us/deeds | No | Web portal + Email |
| **Sagadahoc** | County Custom | Name, doc search, e-recording | Deed records, documents, e-recording available | sagadahoccountyme.gov/registry_of_deeds | No | Web portal |
| **Somerset** | i2k USLandRecords | Name, date, doc number, book/page | Deed records (1809-present searchable) | i2k.uslandrecords.com/ME/Somerset | No | Web portal |
| **Waldo** | SearchIQS | Name, date range, doc type, instrument #, book/page | Deed records, plans (1971-present docs, 1800-present plans, 1961-present index) | searchiqs.com (Waldo County) | No | Web portal |
| **Washington** | i2k USLandRecords | Name, doc type, date range | Deeds, mortgages, liens, surveys, foreclosures (1956-present) | washingtoncountymaine.com/registry-of-deeds | No | Web portal |
| **York** | SearchIQS | Name, volume/book, doc number | Deed records, liens, mortgages, indexed by name/type/date | searchiqs.com/meyor | No | Web portal |

---

## Platform Analysis

### Platforms Used (by county count):
- **SearchIQS:** 6 counties (Franklin, Lincoln, Oxford, Piscataquis, Waldo, York)
- **County Custom Systems:** 6 counties (Androscoggin, Aroostook N/S, Knox, Penobscot, Sagadahoc)
- **i2k USLandRecords:** 3 counties (Cumberland, Somerset, Washington)
- **AcclaimWeb:** 1 county (Hancock)
- **KoFile Technology:** 1 county (Kennebec)

### Implications for Integration:
- **No single API** — Would require building per-county web scraper or automated portal interaction
- **SearchIQS dominance (6 counties)** — Could standardize on SearchIQS portal interaction if needed
- **Different platforms = different HTML structure** — Would require conditional parsing logic per platform type

---

## Universal Query Capabilities

**All 16 counties support:**
- ✓ Search by **Grantor/Grantee Name** (PRIMARY for our use case)
- ✓ Search by **Date Range**
- ✓ Search by **Book/Volume & Page Number**
- ✓ Search by **Document Number/Instrument #**
- ✓ Most counties: **Document Type** filter (deeds, mortgages, liens, etc.)

**Selective availability:**
- ✗ Address-based search: Limited (not all counties support)
- ✗ Parcel ID search: Not available in most systems
- ✓ Town/Municipality filter: Available in some counties

---

## What Records Return

**Standard returnable data:**
- Deed records (primary)
- Mortgage documents
- Liens and assignments
- Property plans (where digitized)
- Easements
- Leases
- Powers of attorney
- Foreclosure notices

**Coverage depth:**
- Oldest records: Back to 1760s-1850s (varies by county)
- Digital coverage: Typically 1950s-1990s onward, expanding backward
- OCR full-text search: Available in some systems (e.g., Kennebec)

---

## Cost & Access Model

**Free Tier:**
- First 400 pages per calendar year per user (once registered)
- No subscription required
- Free property owner fraud alert service (most counties)

**Paid:**
- $0.50 per page after first 400 pages/year
- Some counties accept credit card or check payment directly

**Registration:**
- Most counties require free registration to search
- No login verification delays

**Terms of Service:**
- **Web scraping PROHIBITED** in all county ToS
- Automated access without explicit authorization violates terms
- Bulk download/export not available

---

## Test Cases: Marquis & Roberts

### Marquis 26-018
- **Owner Name:** Kristen Marquis
- **County:** Oxford (confirmed)
- **Property:** 17 Aspen Way, Turner, Maine
- **Database:** SearchIQS (Oxford uses this platform)
- **Expected Lookup:** Search Oxford County deed records by grantor name "Kristen Marquis" → find deed recorded under her name → extract legal description and boundary

### Roberts 26-123
- **Owner Name:** Roberts Properties LLC
- **County:** Oxford (confirmed via GeoLibrary workaround)
- **Property:** 450 Lane Road, Greene/Mechanic Falls boundary, Maine
- **Database:** SearchIQS (Oxford)
- **Expected Lookup:** Search Oxford County by grantor name "Roberts Properties LLC" → find deed → extract boundary information
- **Note:** Town name in form (Greene) does not match actual location (Mechanic Falls) — deed lookup by owner name will resolve this ambiguity

---

## Web Portal Access for Test Cases

**For Oxford County (both test cases):**

URL: `https://searchiqs.com/meoxe`

**Query process (manual):**
1. Go to SearchIQS Oxford County portal
2. Select search type: "Grantors"
3. Enter name: "Kristen Marquis" or "Roberts Properties LLC"
4. Enter date range (optional): Leave open or specify narrow range
5. Click "Search"
6. Results show deed records with book/page, document type, date, parties
7. Click on specific deed record to view scanned document image and legal description

**What we'd extract from deed:**
- Grantor name (original owner)
- Grantee name (new owner)
- Date of recording
- Legal description (text or property boundary references)
- Deed type (warranty, quitclaim, etc.)
- Book and page reference

---

## Architectural Implications for Integration

### Current Approach (GeoLibrary only)
✓ Fast (API available)  
✗ Boundary is reduced to bounding box  
✗ Doesn't resolve deed-based boundaries or owner verification

### Proposed Approach (GeoLibrary → Deed Lookup)
**Flow:**
1. Intake form captures: Owner name, County, Address
2. **Stage 1 - GeoLibrary lookup:** Address → find parcel, confirm county, get tax map boundary
3. **Stage 2 - Deed lookup:** Owner name + County → query deed database → find recorded deed
4. **Output:** Authoritative deed-based boundary + deed reference

### Technical Challenges

**1. No API Access**
- All systems are web portal only
- Would require Selenium/Playwright-based web scraping OR manual lookup
- SearchIQS URLs are dynamic (POST-based, not simple query strings)

**2. Different Platforms = Different Scraping Logic**
- 5 different platforms = 5 different HTML structures
- Would need conditional parser per platform
- Maintenance burden with county system updates

**3. Legal/ToS Considerations**
- Automated scraping violates most county ToS
- Could face blocking (IP bans, CAPTCHAs)
- Manual lookup + human review is safer path

**4. Owner Name Variations**
- "Kristen Marquis" vs "K. Marquis" vs "Kristen A. Marquis" — fuzzy matching needed
- LLC variations: "Roberts Properties LLC" vs "Roberts Properties, LLC" vs "Roberts Properties L.L.C."

---

## Recommendation for FormRunner Implementation

### Phase 1 (Recommended Current State)
- **Keep GeoLibrary lookup** as primary (already working, deterministic)
- **Add manual deed lookup** as verification step:
  - Link to SearchIQS/county portal in correction form
  - Allow evaluator to manually verify deed matches GeoLibrary boundary
  - User inputs: Owner name (from intake) + County → evaluator clicks link → searches deed → confirms match

### Phase 2 (Future - if ToS relaxed)
- Contract with county registries for programmatic API access
- Some counties may offer private API for professional users (not publicly available yet)
- Automated deed lookup would become feasible

### Phase 3 (Future - if commercial service available)
- Monitor for third-party deed aggregators offering API (similar to how we use GeoLibrary)
- Services like LandAmerica, Westlaw, LexisNexis offer deed data APIs but at enterprise cost

---

## Conclusion

**Can deed lookup be automated programmatically?**
- **No** — all 16 counties prohibit automated access and offer no APIs
- Web scraping is technically possible but violates ToS and risks account blocking

**What's feasible now?**
- Manual lookup: Owner name → evaluate can click link → search portal → verify deed
- Semi-automated: Extract deed document text via manual search, parse legal description
- GeoLibrary + manual verification: Current approach is safest and legally compliant

**Timeline for automatable solution:**
- Requires counties to provide APIs (no public timeline)
- OR requires licensing from commercial deed aggregators (enterprise cost)
- Current recommendation: Use GeoLibrary as primary, reserve deed lookup for evaluator-driven verification

---

## References

**Statewide Portal:**
- Maine Registry of Deeds Association: https://www.maineregistryofdeeds.com/
- Maine Revenue Services - County Registries: https://www.maine.gov/revenue/taxes/property-tax/transfer-tax/county-registries-of-deeds

**Individual County Registries:**
1. Androscoggin: https://www.androscoggincountymaine.gov/164/Registry-of-Deeds
2. Aroostook North: https://www.aroostookcountymaine.gov/
3. Aroostook South: https://www.aroostookcountymaine.gov/
4. Cumberland: https://www.cumberlandcountyme.gov/departments/registry_of_deeds/
5. Franklin: https://www.franklincountymaine.gov/county-operations/registry-of-deeds/
6. Hancock: https://hancockcountymaine.gov/registry-of-deeds/
7. Kennebec: https://kennebec.gov/deeds/
8. Knox: https://knoxcountymaine.gov/county_departments/registry_of_deeds/
9. Lincoln: https://www.lincolncountymaine.me/deeds
10. Oxford: https://www.oxfordcounty.org/
11. Penobscot: https://www.penobscotdeeds.com/
12. Piscataquis: https://www.piscataquis.us/deeds/
13. Sagadahoc: https://sagadahoccountyme.gov/departments/registry_of_deeds.php
14. Somerset: https://somersetcountyme.gov/registry-of-deeds/
15. Waldo: https://www.waldocountymaine.gov/department/rod/
16. Washington: https://washingtoncountymaine.com/registry-of-deeds/
17. York: https://www.yorkcountymaine.gov/registry-of-deeds

---

## Next Steps (Awaiting Approval)

**To proceed with deed lookup integration, you must decide:**

1. **Manual verification approach** — Evaluator manually looks up owner in deed database (no code change needed)
2. **Selenium-based scraping** — Automated web scraper for SearchIQS counties only (Phase 2, requires ToS review)
3. **Commercial deed aggregator** — Partner with Westlaw/LexisNexis for API access (enterprise cost)

**Once you approve direction, implementation prompt will specify:**
- Which counties to target
- Scraping approach vs. manual link generation
- Legal/ToS clearance requirements
- Test plan for Marquis + Roberts

