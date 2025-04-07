'''
This script is intended to be run as part of a GitHub Actions workflow, but you can also
run it locally setting inputs as environment variables:

GITHUB_OUTPUT=github_outputs.txt python getRandomPair.py
'''
import asf_search as asf
import geopandas as gpd
import json
import os

print(os.getcwd())

# 58045 -> 48 coords, & CCW for NASA CMR
gfa = gpd.read_file('nepal.geojson') 
gfa = gfa.simplify(0.1).reverse() 

asf.constants.INTERNAL.CMR_TIMEOUT = 120
results = asf.search(platform=[asf.PLATFORM.SENTINEL1], 
                    processingLevel=asf.PRODUCT_TYPE.BURST,
                    intersectsWith=str(gfa.geometry.values[0]),
                    # Restrict to Fufiters date range  2017–2024?
                    start="2024-01-01",
                    # NOTE: returns most recent acquisitions
                    maxResults=500,
                    )
                    
gf = gpd.GeoDataFrame.from_features(results.geojson(), crs=4326)
gf['fullBurstID'] = gf.burst.str['fullBurstID']
random_burst = gf.fullBurstID.sample(1).values[0]

# Get burst stack
results = asf.search(platform=[asf.PLATFORM.SENTINEL1], 
                    processingLevel=asf.PRODUCT_TYPE.BURST,
                    fullBurstID=random_burst
                    )
acquisitions = gpd.GeoDataFrame.from_features(results.geojson(), crs=4326)
random_pol = acquisitions.polarization.sample(1).values[0]
pair = acquisitions[acquisitions.polarization == random_pol].sample(2)
# Original SLC names
reference, secondary = pair.additionalUrls.apply(lambda x: x[0].split('/')[3])

# Save Environment Variables for Next Job
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    print(f'REFERENCE={reference}', file=f)
    print(f'SECONDARY={secondary}', file=f)
    print(f'BURSTID={random_burst}', file=f)
    print(f'POLARIZATION={random_pol}', file=f)