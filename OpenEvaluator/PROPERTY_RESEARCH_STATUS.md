# Property Research Integration - Status

## ✅ What's Complete

1. **Pipeline Foundation**
   - Reverted to `professional_drawings.py` (produces structured output)
   - Updated `integrate_professional_drawings.py` to accept enriched property data
   - Pipeline now extracts property identifiers automatically from submission

2. **Property Extraction** 
   - Extracts from form: Address, Town, Map, Lot, Acreage
   - Example: "17 Aspen Way, Turner, Maine" + "Map 26 Lot 18"
   - Logs what research is needed

3. **Research Infrastructure**
   - `enrich_property_data.py` - Structures research tasks
   - `search_maine_property_data.py` - Search and parsing templates
   - Generated Hermes task descriptions

## 🎯 Current State: Example Property

**Property:** 17 Aspen Way, Turner, Maine  
**Map & Lot:** 26-18  
**Acreage:** 2.35  

**Research Needed (Priority Order):**

### HIGH PRIORITY
1. **Property Boundary** (Required for realistic site plan)
   - Need: Lot boundary polygon coordinates
   - Search: "Map 26-18" Turner Maine GIS property boundary
   - Source: County GIS, town assessor, or deed records

2. **Road Information** (Needed to label and position road)
   - Need: Road name ("Aspen Way"), public/private, distance from house
   - Search: "17 Aspen Way" Turner Maine road frontage
   - Source: Property deed, tax map, assessor record

### MEDIUM PRIORITY  
3. **Zoning & Setbacks** (For setback visualization)
   - Need: Required setback distances (road, property line, well)
   - Search: Turner Maine zoning ordinances residential setback
   - Source: Municipal zoning code

4. **Lot Dimensions** (For accurate lot representation)
   - Need: Road frontage (ft), depth (ft), shape
   - Search: "Map 26-18" Turner Maine lot dimensions
   - Source: Tax assessor, deed, property record

## 🔄 Next Steps (Choose One)

### Option A: I Research the Property (Fastest)
```
1. Use web search tools to find Maine property records
2. Parse tax assessor, GIS, and zoning data
3. Extract boundary coordinates, road info, setback requirements
4. Feed enriched data to professional_drawings.py
5. Test output against pinnacle examples
```

### Option B: You Provide Property Data
```
1. Provide: Property boundary vertices (coordinates)
2. Provide: Road name and distance information
3. Provide: Setback requirements for Turner zoning
4. I update professional_drawings.py to use the data
5. Test output
```

### Option C: Set Up Hermes to Research
```
1. Provide task descriptions to Hermes
2. Hermes searches and parses online sources
3. Returns structured property data
4. Feeds into pipeline automatically
```

## 📋 What Each Option Delivers

Once property data is provided (via A, B, or C), the drawings will have:

✅ Real property boundary (polygon instead of generic rectangle)  
✅ Actual road name and position  
✅ Real setback distances (visualized on plan)  
✅ Accurate lot dimensions and shape  
✅ Professional appearance like the pinnacle examples  

## 📁 Key Files

- `integrate_professional_drawings.py` - Main entry point
- `enrich_property_data.py` - Extracts and structures research
- `search_maine_property_data.py` - Search templates
- `professional_drawings.py` - Drawing generator (ready for enriched data)
- `run_pipeline.py` - Main pipeline (already integrated)

## 🚀 Recommendation

**Option A** is best because:
- Fastest path to testing
- Can verify approach works
- No manual data entry
- Can then automate for all properties via Hermes

Ready to proceed when you give the signal!
