#! /usr/bin/env python
"""
Search ASF for SLCs containing a specific burst

Usage: findSLCs.py BurstID
Example: findSLCs.py 135_289664_IW1

"""
import argparse
import asf_search as asf
import geopandas as gpd


def get_burst_metadata(burstID):
    print('Searching for Burst Metdata...')
    results = asf.granule_search([f'S1_{burstID}-BURSTMAP'])
    gfB = gpd.GeoDataFrame.from_features(results.geojson(), crs=4326)
    gfB["burstID"] = gfB.fileID.str[3:-9]
    gfB = gfB.dropna(axis='columns')
    print(gfB.iloc[0])
    
    return gfB


def search_for_slcs(gfB, start, end):
    print('Searching for ASF for SLCs...')
    burst = gfB.iloc[0]
    results = asf.geo_search(
                    platform=[asf.PLATFORM.SENTINEL1],
                    processingLevel='SLC', #or BURST from 2023 onwards for select paths 
                    beamMode=asf.BEAMMODE.IW,
                    relativeOrbit=burst.pathNumber,
                    intersectsWith=f"POINT({burst.centerLon} {burst.centerLat})",
                    start=start,
                    end=end,
                    )
    
    gf = gpd.GeoDataFrame.from_features(results.geojson(), crs=4326)
    gf['datetime'] = gpd.pd.to_datetime(gf['startTime'])
    
    print('BurstID:', burst.burstID)
    print('Number of SLCs:', len(gf))
    print('Timespan:', gf.startTime.iloc[0], gf.startTime.iloc[-1])
    print('Polarizations:', list(gf.polarization.unique()))
    print('platforms:', list(gf.platform.unique()))
    s = gf.datetime.diff(-1).dt.round('1d').dt.days.dropna().astype('i2')
    print('Temporal separation (min, mode, max days):', s.min(),  s.mode()[0], s.max())

    return gf


def slippy_map(gf, gfB):
    """Plot geopandas polygons using folium and open in browser"""
    # Interactive map from CLI
    import webbrowser
    import folium
    from folium.plugins import MiniMap
    path = '/tmp/mapSLCs.html'
    m = gf.drop(columns='datetime').explore(tiles='Esri.WorldImagery', color='cyan', style_kwds=dict(fill=None))
    gfB.explore(m=m, column='burstID', cmap=['magenta'], legend=True)
    MiniMap(position="topright").add_to(m)
    m.save(path)
    print('map saved to', path)
    webbrowser.open(f'file://{path}')


def timeline(gf, burstID):
    """ Plot timeline of SLC acquisitions """
    # Interactive map from CLI
    import matplotlib.pyplot as plt
    plt.figure(figsize=(11,4))
    plt.scatter(gf.datetime, gf.platform, marker='|', color='k') 
    plt.title(burstID)
    plt.plot()
    plt.show()
    #plt.savefig(f'/tmp/{burstID}-timeline.pdf')


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Search ASF for burstIDs that cover a point"
    )
    parser.add_argument("burstID", type=str, help="BurstID (e.g. 106_227373_IW2)")
    parser.add_argument("-s", "--start", default=None, type=str, help="Start date (e.g. 2017-01-01)")
    parser.add_argument("-e", "--end", default=None, type=str, help="End date (e.g. 2023-01-01)")
    parser.add_argument("-g", "--geojson", default=False, action="store_true", help="Save GeoJSON metadata")
    parser.add_argument("-p", "--show-plots", default=False, action="store_true", help="Show map of SLC footprints")

    args = parser.parse_args()
    # if args.start == 'None':
    #     args.start = None
    print(args)

    gfB = get_burst_metadata(args.burstID)
    gf = search_for_slcs(gfB, args.start, args.end)

    # Dump entire list of SLCs
    print('------------------------------------')
    print('\n'.join(gf.sceneName.to_list()))

    if args.geojson:
        # Drop lists before saving to GeoJSON
        gf.drop(columns='s3Urls').to_file(f'/tmp/{args.burstID}.geojson', driver='GeoJSON')

    if args.show_plots:
        slippy_map(gf, gfB)
        timeline(gf, args.burstID)
