import ee

try:
    ee.Initialize(project='red-provider-454106-h8')
    print("Google Earth Engine Initialized Successfully (Ultimate Dual-Core Version).")
except Exception as e:
    print(f"GEE Initialization Failed: {e}")
    raise e

# --- 1. Data Acquisition ---
def get_s1_collection(geometry, start_date, end_date):
    """Gets and filters the Sentinel-1 GRD ImageCollection."""
    return (ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(geometry)
            .filterDate(ee.Date(start_date), ee.Date(end_date))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
            .filter(ee.Filter.eq('instrumentMode', 'IW')))

def get_s2_collection(geometry, start_date, end_date):
    """Gets, filters, and masks clouds in the Sentinel-2 SR ImageCollection."""
    def mask_s2_clouds(image):
        # Sentinel-2 L2A data products have different QA band names.
        # 'QA60' is common, but 'SCL' (Scene Classification Layer) is more robust if available.
        # We will try to be robust against different product versions.
        qa = image.select('QA60')
        # Bits 10 and 11 are clouds and cirrus, respectively.
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        return image.updateMask(mask).divide(10000).select("B.*")
    
    return (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') # Use Harmonized collection for consistency
            .filterBounds(geometry)
            .filterDate(ee.Date(start_date), ee.Date(end_date))
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50)) # Loosen cloud filter a bit
            .map(mask_s2_clouds))

# --- 2. Ultimate Analysis Algorithms ---

def analyze_flood_ultimate(geometry, analysis_date, before_days=90, after_days=15):
    """
    Ultimate flood analysis function with defensive data checks and robust algorithms.
    """
    analysisDate = ee.Date(analysis_date)
    beforeStart, beforeEnd = analysisDate.advance(-before_days, 'day'), analysisDate.advance(-1, 'day')
    afterStart, afterEnd = analysisDate, analysisDate.advance(after_days, 'day')

    # Defensive Data Check 1: Historical data
    historical_collection = get_s1_collection(geometry, beforeStart, beforeEnd)
    if historical_collection.size().getInfo() == 0:
        raise ee.EEException(f"Data Availability Error: No Sentinel-1 images found in the historical period ({beforeStart.format().getInfo()} to {beforeEnd.format().getInfo()}).")

    # Defensive Data Check 2: Analysis data
    target_collection = get_s1_collection(geometry, afterStart, afterEnd)
    if target_collection.size().getInfo() == 0:
        raise ee.EEException(f"Data Availability Error: No Sentinel-1 images found in the analysis period ({afterStart.format().getInfo()} to {afterEnd.format().getInfo()}).")

    before_image = historical_collection.median().clip(geometry)
    after_image = target_collection.median().clip(geometry)
    
    before_filtered = before_image.focal_median(3, 'circle', 'pixels')
    after_filtered = after_image.focal_median(3, 'circle', 'pixels')
    
    difference = after_filtered.subtract(before_filtered)
    flood_mask1 = difference.select('VH').lt(-3)
    flood_mask2 = after_filtered.select('VH').lt(-15)
    combined_flood = flood_mask1.And(flood_mask2)
    
    flood_smoothed = combined_flood.focal_mode(1.5, 'circle', 'pixels', 2).focal_max(1, 'circle', 'pixels', 1)
    
    jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
    permanent_water = jrc.gt(50)
    final_flood_mask = flood_smoothed.And(permanent_water.Not())
    
    return {'final_flood_mask': final_flood_mask.selfMask().rename('flood_mask')}

def analyze_deforestation_between_periods(geometry, start_date_period1, end_date_period1, start_date_period2, end_date_period2):
    """
    Compares two distinct periods to find deforestation, a robust "Then vs. Now" approach.
    """
    s1_period1 = get_s1_collection(geometry, start_date_period1, end_date_period1)
    s2_period1 = get_s2_collection(geometry, start_date_period1, end_date_period1)

    s1_period2 = get_s1_collection(geometry, start_date_period2, end_date_period2)
    s2_period2 = get_s2_collection(geometry, start_date_period2, end_date_period2)

    if s1_period1.size().getInfo() == 0 or s2_period1.size().getInfo() == 0 or s1_period2.size().getInfo() == 0 or s2_period2.size().getInfo() == 0:
        raise ee.EEException("Insufficient imagery in one of the comparison periods. Cloud cover may be too high or data may be unavailable.")

    s1_period1_median = s1_period1.median()
    s2_period1_median = s2_period1.median()
    s1_period2_median = s1_period2.median()
    s2_period2_median = s2_period2.median()

    backscatter_drop = s1_period1_median.select('VV').subtract(s1_period2_median.select('VV')).gt(3)

    ndvi_period1 = s2_period1_median.normalizedDifference(['B8', 'B4'])
    ndvi_period2 = s2_period2_median.normalizedDifference(['B8', 'B4'])
    optical_loss = ndvi_period1.subtract(ndvi_period2).gt(0.25)
    
    deforestation_mask = backscatter_drop.And(optical_loss)
    return deforestation_mask.selfMask().rename('deforestation_mask')

# --- 3. Utility Functions ---
def get_tile_url(ee_image, vis_params):
    """Generates a tile URL for a given EE Image."""
    map_id = ee_image.getMapId(vis_params)
    return map_id['tile_fetcher'].url_format

def get_area_stats(change_image, geometry):
    """Calculates the area of change in square meters, robustly handles empty images."""
    area_image = change_image.multiply(ee.Image.pixelArea())
    stats = area_image.reduceRegion(
        reducer=ee.Reducer.sum(), 
        geometry=geometry, 
        scale=30, 
        maxPixels=1e9, 
        bestEffort=True
    )
    
    stats_info = stats.getInfo()
    band_name = change_image.bandNames().get(0).getInfo()
    if not stats_info or not stats_info.get(band_name):
        return 0 
        
    area_sq_m = stats.values().get(0).getInfo()
    return area_sq_m if area_sq_m else 0