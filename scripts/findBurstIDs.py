#! /usr/bin/env python
"""
Search ASF for burstIDs that cover a point

Usage: findBurstIDs.py LON LAT
Example: findBurstIDs.py -73.604 -49.669
"""
import argparse
import asf_search as asf
import geopandas as gpd


def find_bursts(lon, lat):
    """Find ESA Sentinel-1 burstIDs that cover a point"""
    results = asf.geo_search(
        collections="C2450786986-ASF",
        # NOTE: collection doesn't expose beamMode, so need to filter results instead
        # beamMode=asf.BEAMMODE.IW,
        intersectsWith=f"POINT({lon} {lat})",
    )
    gf = gpd.GeoDataFrame.from_features(results.geojson(), crs=4326)

    gf = gf[gf.fileID.str.contains("_IW")].reset_index(drop=True)
    # Standard Name (PATH_ID_SWATH)
    gf["burstID"] = gf.fileID.str[3:-9]
    gf = gf.dropna(axis='columns')
    gf = gf.drop(columns='s3Urls')
    print(gf.loc[:, ["burstID", "flightDirection"]])
    
    return gf

def slippy_map(gf, lon, lat):
    """Plot geopandas polygons using folium and open in browser"""
    # Interactive map from CLI
    import webbrowser
    import folium
    from folium.plugins import MiniMap
    path = '/tmp/map.html'
    m = gf.explore(column='burstID', tiles='Esri.WorldImagery', categorical=True, cmap='Accent')
    folium.Marker(location=[lat, lon]).add_to(m)
    MiniMap(position="topright", zoom_level_fixed=1).add_to(m)
    m.save(path)
    print('map saved to', path)
    webbrowser.open(f'file://{path}')


def static_map(gf, lon, lat):
    """Plot geopandas polygons using matplotlib"""
    import matplotlib.pyplot as plt
    import contextily as cx

    fig, ax = plt.subplots(figsize=(11,8.5))
    gf.plot(ax=ax, column="burstID", facecolor="none", linewidth=4, cmap='Accent', legend=True)
    ax.plot(lon, lat, "k*", markersize=10)
    
    # Zoom out more compared to autoscaling defaults for more context
    percent_buffer = .25
    xmin,ymin,xmax,ymax = gf.total_bounds
    xbuf = (xmax - xmin) * percent_buffer
    ybuf = (ymax - ymin) * percent_buffer
    ax.set_xlim(xmin - xbuf, xmax + xbuf)
    ax.set_ylim(ymin - ybuf, ymax + ybuf)
    # Automatically chosen zoom can be a bit coarse, zoom=9 seems good, or zoom_adjust=1
    cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, crs='EPSG:4326', zoom_adjust=1)  # WorldTerrain

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Sentinel-1 Bursts Intersecting ({lon}, {lat})")
    plt.save('/tmp/footprints.png')
    plt.show()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Search ASF for burstIDs that cover a point"
    )
    parser.add_argument("lon", type=float, help="Longitude")
    parser.add_argument("lat", type=float, help="Latitude")
    parser.add_argument("-p", "--show-plot", default=False, action="store_true", help="Plot burstIDs on a map")
    #parser.add_argument("-t", "--show-slcs", default=False, action="store_true", help="Lookup all SLCs for burstIDs")
    args = parser.parse_args()
    #print(args)
    gf = find_bursts(args.lon, args.lat)

    if args.show_plot:
        #static_map(gf, args.lon, args.lat)
        slippy_map(gf, args.lon, args.lat)

