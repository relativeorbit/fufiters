from datetime import datetime
from typing import Any, Dict

import glob
import re

import pystac
from pystac.utils import str_to_datetime
from pystac import Extent, ProviderRole, SpatialExtent, TemporalExtent
from pystac.extensions import sar
from pystac.link import Link
from pystac import Summaries
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterBand, RasterExtension
from pystac.extensions.sar import SarExtension
from pystac.extensions.sat import OrbitState, SatExtension

import rasterio

import xml.etree.ElementTree as ET

# Import extension version
from rio_stac.stac import PROJECTION_EXT_VERSION, RASTER_EXT_VERSION

# Import rio_stac methods
from rio_stac.stac import (
    get_dataset_geom,
    get_projection_info,
    #get_raster_info,
    #get_eobands_info,
    bbox_to_geom,
    #get_media_type
)



def hyp32stac():
    ''' convert ASF HYP3 Ouput to STAC ITEM
    assumes single hyp3isce output folder in current directory (S1_023790_IW1_20230621_20230703_VV_INT80_6983)
    '''
    outdir = glob.glob('S1_*[!zip]')[0]
    prefix = outdir[14:31]

    # Parse Product File
    with open(f'{outdir}/{outdir}.txt') as f:
        lines = [x.rstrip() for x in f.readlines()]
        meta = dict([x.split(': ') for x in lines])
    
    ref = meta['Reference Granule']
    sec = meta['Secondary Granule']

    # Get Relative Orbit for unique BurstID
    manifest_path = glob.glob('*/manifest.safe')[0]
    tree = ET.parse(manifest_path)
    ns = {'safe': 'http://www.esa.int/safe/sentinel-1.0'}
    relative_orbit_number = tree.find('.//safe:relativeOrbitNumber[@type="start"]', ns).text.zfill(3)
    ESABurstId = f'{relative_orbit_number}{ref[2:13]}'

    # get root url (if processed by ASF HYP3)
    #url = job.files[0]['url']
    #outdir = job.files[0]['filename'].rstrip('.zip')
    #gdal_path = f'/vsizip//vsicurl/{url}/{outdir}/{outdir}'
    #print(gdal_path)

    # remote files
    remote_root = f's3://fufiters/{ESABurstId}/{prefix}/{outdir}'
    gdal_path = f'{remote_root}/{outdir}'
    #remote_https = remote_root.replace('s3://fufiters','https://fufiters.s3.amazonaws.com/')

    # Parse processing timestamps
    pattern = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    with open('isce.log') as f:
        lines = [x[:20] for x in f.readlines()]
        matches = [re.match(pattern,x) for x in lines]
        timestamps = [x.group() for x in matches if x != None]

    # Mapping of assets
    assets = [ 
        {"name": "conncomp", "href": gdal_path+'_conncomp.tif', "role": ['data'], "type":pystac.MediaType.COG},
        {"name": "corr", "href": gdal_path+'_corr.tif', "role": ['data'], "type":pystac.MediaType.COG},
        {"name": "dem", "href": gdal_path+'_dem.tif', "role": ['data'], "type":pystac.MediaType.COG},
        {"name": "lv_phi", "href": gdal_path+'_lv_phi.tif', "role": ['data'], "type":pystac.MediaType.COG},
        {"name": "lv_theta", "href": gdal_path+'_lv_theta.tif', "role": ['data'], "type":pystac.MediaType.COG},
        {"name": "unwrapped", "href": gdal_path+'_unw_phase.tif', "role": ['data'], "type":pystac.MediaType.COG},
        {"name": "wrapped", "href": gdal_path+'_wrapped_phase.tif', "role": ['data'], "type":pystac.MediaType.COG},
        #{"name": "browse", "href": job.browse_images[0], "role": ['overview'], "type":pystac.MediaType.PNG},
        #{"name": "thumbnail", "href": job.thumbnail_images[0], "role": ['thumbnail'], "type":pystac.MediaType.PNG},
        {"name": "metadata", "href": gdal_path+'.txt', "role": ['metadata'], "type":pystac.MediaType.TEXT},
        # Add custom outputs
        {"name": "azimuth_offsets", "href": gdal_path+'_azi_off.tif', "role": ['metadata'], "type":pystac.MediaType.COG},
        {"name": "range_offsets", "href": gdal_path+'_rng_off.tif', "role": ['metadata'], "type":pystac.MediaType.COG},
    ]

    # Assume all tifs same dimensions
    with rasterio.open(f'./{outdir}/{outdir}_unw_phase.tif') as src_dst:
        # Get BBOX and Footprint
        dataset_geom = get_dataset_geom(src_dst, densify_pts=0, precision=-1)  
        bbox = dataset_geom["bbox"]

        proj_info = {
            f"proj:{name}": value
            for name, value in get_projection_info(src_dst).items()
        }

    pystac_assets = []

    for asset in assets:
        pystac_assets.append(
            (
                asset["name"], 
                pystac.Asset(
                    href=asset["href"],
                    media_type=asset["type"],
                    #extra_fields={
                        #**proj_info, # Put into properties to avoid duplication
                        #**raster_info, #avoid opening all these for now... 
                    #},
                    roles=asset["role"],
                ),
            )
        )

    start = ref.split('_')[3]
    end = sec.split('_')[3]

    # additional properties to add in the item
    properties = dict(
                      start_datetime=str_to_datetime(start).isoformat()+'Z',
                      end_datetime=str_to_datetime(end).isoformat()+'Z',
                      processingDate=str_to_datetime(timestamps[0]).isoformat()+'Z',
                      burstId=ESABurstId,
                      passDirection=meta['Reference Pass Direction'],
                      perpendicularBaseline=meta['Baseline'],
                      demSource=meta['DEM source'],
                      granules=[ref,sec],
                     )
    #properties['sat:orbit_state']=row.flightDirection.lower()
    # Add projection information 
    properties.update(proj_info)            

    # WARNING: only works for non-redundant time series
    input_datetime = str_to_datetime(start)

    # STAC Item Id
    id = outdir

    # name of collection the item belongs to
    #collection = 'OPERA_L2_RTC'
    #collection_url = None

    extensions =[
        f"https://stac-extensions.github.io/projection/{PROJECTION_EXT_VERSION}/schema.json", 
        #f"https://stac-extensions.github.io/raster/{RASTER_EXT_VERSION}/schema.json",
    ]
    
    # item
    item = pystac.Item(
        id=id,
        geometry=bbox_to_geom(bbox),
        bbox=bbox,
        # collection=collection,
        stac_extensions=extensions,
        datetime=input_datetime,
        properties=properties,
    )

    for key, asset in pystac_assets:
        item.add_asset(key=key, asset=asset)

    #item.validate()
    # just save rather than retun
    
    # relative paths in item:
    # "href": "./S1_023790_IW1_20230621_20230703_VV_INT80_4182/S1_023790_IW1_20230621_20230703_VV_INT80_4182_rng_off.tif
    #item.set_self_href(f'{remote_root}/{outdir}.json')
    item.save_object(dest_href=f'./{outdir}/{outdir}.json')

    #return item


# NOTE: copied from https://github.com/stactools-packages/sentinel1/blob/main/src/stactools/sentinel1/rtc/constants.py
# General Sentinel-1 Constants
SENTINEL_LICENSE = Link(
    rel="license",
    target="https://sentinel.esa.int/documents/"
    + "247904/690755/Sentinel_Data_Legal_Notice",
)

SENTINEL_INSTRUMENTS = ["c-sar"]
SENTINEL_CONSTELLATION = "sentinel-1"
SENTINEL_PLATFORMS = ["sentinel-1a", "sentinel-1b"]
SENTINEL_FREQUENCY_BAND = sar.FrequencyBand.C
SENTINEL_CENTER_FREQUENCY = 5.405
SENTINEL_OBSERVATION_DIRECTION = sar.ObservationDirection.RIGHT

SENTINEL_PROVIDER = pystac.Provider(
    name="ESA",
    roles=[ProviderRole.LICENSOR, ProviderRole.PRODUCER],
    url="https://sentinel.esa.int/web/sentinel/missions/sentinel-1",
)

SENTINEL_LICENSE = Link(
    rel="license", target="https://spacedata.copernicus.eu/data-offer/legal-documents"
)

SENTINEL_BURST_PROVIDER = pystac.Provider(
    name="ASF DAAC",
    roles=[ProviderRole.LICENSOR, ProviderRole.PROCESSOR, ProviderRole.HOST],
    url="https://hyp3-docs.asf.alaska.edu/guides/burst_insar_product_guide/",
    extra_fields={
        "processing:level": "L3",
        "processing:lineage": "ASF DAAC HyP3 2023 using the hyp3_isce2 plugin version 0.9.2 running ISCE release 2.6.3",  # noqa: E501
        "processing:software": {"ISCE2": "2.6.3"},
    },
)

SENTINEL_BURST_LICENSE = Link(
    rel="license", target="https://doi.org/10.5281/zenodo.8007397"
)

SENTINEL_BURST_DESCRIPTION = "SAR Interferometry (InSAR) products and their associated files. The source data for these products are Sentinel-1 bursts, extracted from Single Look Complex (SLC) products processed by ESA, and they were processed using InSAR Scientific Computing Environment version 2 (ISCE2) software."  # noqa: E501

# NOTE: GLobal forward processing of available bursts started June 2023
# Select areas have more available back to S1A data availability of October 2014!
SENTINEL_BURST_START: datetime = str_to_datetime("2019-01-01T00:00:00Z")
SENTINEL_BURST_EXTENT = Extent(
    SpatialExtent([-180, -90, 180, 90]),
    TemporalExtent([[SENTINEL_BURST_START, None]]),
)

# NOTE: so far, just working with 10
#utm_zones = ["10"]#, "11", "12", "13", "14", "15", "16", "17", "18", "19"]
# SENTINEL_BURST_EPSGS = [int(f"326{x}") for x in utm_zones]

SENTINEL_BURST_SAR: Dict[str, Any] = {
    "instrument_mode": "IW",
    "product_type": "UNW",
    "polarizations": [sar.Polarization.VV],
    "looks_range": 5,
    "looks_azimuth": 1,
    "gsd": 20,  # final MGRS pixel posting
}


def create_collection(collection_id):
    ''' aggregate summary of items at collection level '''
    summary_dict = {
        "constellation": [SENTINEL_CONSTELLATION],
        "platform": SENTINEL_PLATFORMS,
        "gsd": [SENTINEL_BURST_SAR["gsd"]],
        # "proj:epsg": SENTINEL_BURST_EPSGS,
    }

    collection = pystac.Collection(
        id=collection_id, # NOTE: required?
        description=SENTINEL_BURST_DESCRIPTION,
        extent=SENTINEL_BURST_EXTENT,
        title="ASF S1 BURST INTERFEROGRAMS",
        stac_extensions=[
            SarExtension.get_schema_uri(),
            SatExtension.get_schema_uri(),
            ProjectionExtension.get_schema_uri(),
            RasterExtension.get_schema_uri(),
            # Can use pystac.extensions once implemented
            "https://stac-extensions.github.io/processing/v1.0.0/schema.json",
            "https://stac-extensions.github.io/mgrs/v1.0.0/schema.json",
        ],
        keywords=["sentinel", "copernicus", "esa", "sar"],
        providers=[SENTINEL_PROVIDER, SENTINEL_BURST_PROVIDER],
        summaries=Summaries(summary_dict),
    )
    
    return collection


if __name__ == '__main__':
    hyp32stac()