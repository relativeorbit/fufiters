import asf_search as asf
import fsspec
import geopandas as gpd
import json
import os

# Parse Workflow inputs from environment variables
START = int(os.environ['Year'])
END = START+1
POL = os.environ['Polarization']
FULLBURSTID = os.environ['FullBurstId']
RELORB,BURSTID,SUBSWATH = FULLBURSTID.split('_')

# Get centroid of burst from database 
url = 'https://github.com/relativeorbit/s1burstids/raw/main/burst_map_IW_000001_375887_brotli.parquet'
with fsspec.open(url) as file:
    gfb = gpd.read_parquet(file,
                        filters=[('burst_id', '=', int(BURSTID)),
                                    ('subswath_name', '=', SUBSWATH)]
                        )

# Search for SLCs
results = asf.search(platform=[asf.PLATFORM.SENTINEL1], 
                    processingLevel=asf.SLC, 
                    beamMode=asf.BEAMMODE.IW,
                    intersectsWith=gfb.iloc[0].geometry.centroid.wkt,
                    relativeOrbit=int(RELORB),
                    start=f"{START}-01-01",
                    end=f"{END}-01-01",
                    )

# For case of frame overlap, ensure SLCs contain full burst
def get_overlap_area(gf, gfREF):
# want frames with > 10% overlap
frame_area = gfREF.iloc[0].geometry.area
overlaps = gf.geometry.map(lambda x: x.intersection(gfREF.geometry.iloc[0]).area/frame_area)

return overlaps

gf['overlap'] = get_overlap_area(gf, gfb)
gf = gf.query('overlap >= 0.95').reset_index(drop=True)

print('Number of Acquisitions: ', len(results))
burstIDs = gf.sceneName.to_list()
burstIDs.sort()
print('\n'.join(burstIDs))

# Create Matrix Job Mapping (JSON Array)
# NOTE: only up to (current-npairs) for sufficient connections & precise orbits
pairs = []
for r in range(len(burstIDs) - ${{ inputs.npairs }}):
for s in range(1, ${{ inputs.npairs }} + 1 ):
    ref = burstIDs[r]
    sec = burstIDs[r+s]
    shortname = f'{ref[14:22]}_{sec[14:22]}'
    pairs.append({'reference': ref, 'secondary': sec, 'name':shortname})
matrixJSON = f'{{"include":{json.dumps(pairs)}}}'
print(f'Number of Interferograms: {len(pairs)}')

with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
print(f'BURST_IDS={burstIDs}', file=f)
print(f'MATRIX_PARAMS_COMBINATIONS={matrixJSON}', file=f)