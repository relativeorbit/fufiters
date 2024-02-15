# Fufiters

A combined InSAR, pixel-offsets workflow for measuring elevation change in Nepal using [Sentinel-1 Synthethic Aperture Radar bursts](https://asf.alaska.edu/datasets/data-sets/derived-data-sets/sentinel-1-bursts/)

## Design

Run a modified version of [hyp3-isce2](https://github.com/ASFHyP3/hyp3-isce2) to generate an inventory of inteferograms and pixel offset maps for a given Sentinel-1 burst. Workflows are written using Python scripts and GitHub Actions for concurrent batch processing on Microsoft Azure.

[Resuable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows) are composed to run processing of a single image pair, to processing all pairs over all available years in parallel (Sentinel-1 acquisitions start in October 2014). 

At a minimum you need to select a Sentinel-1 Burst. You can search for Burst IDs using [NASA Earthdata Search](https://search.earthdata.nasa.gov/search/granules?p=C2450786986-ASF&pg[0][v]=f&pg[0][id]=*IW*&pg[0][gsk]=-start_date&g=G2453394254-ASF&q=burst&sb[0]=80.82422%2C26.11576%2C87.97852%2C30.47298&tl=1708033475.92!3!!&lat=25.619422925906335&long=78.22265625&zoom=5)

## Instructions

Install the [GitHub actions CLI](https://cli.github.com) in order to easily run workflows from the command line. Alternatively you can manually run workflows from the 'Actions' repository tab. NOTE: you must be a member of this GitHub organization to run these workflows, or you can fork this repository and add your own secrets (see below).

Optional inputs for all workflows: 
```
nlooks=5x1 [20x4, 10x2]
polarization=VV [HH]
```

#### Generate a single burst interferogram: 

Use the full SLC names and specify the full burstId (`[Track]_[Burst]_[Subswath]`) that you want to process:

```
gh -R relativeorbit/fufiters workflow run singleburst_SLC.yml \
  -f reference=S1A_IW_SLC__1SDV_20190101T121401_20190101T121429_025284_02CBEB_65D7 \
  -f secondary=S1A_IW_SLC__1SDV_20190113T121401_20190113T121429_025459_02D234_3311 \
  -f burstId=012_023790_IW1  
```
Note: to select SLC names you can use https://search.asf.alaska.edu or use ASF's Python Client https://github.com/asfadmin/Discovery-asf_search


#### Generate a set of interferograms for all years


This workflow will do the search automatically and create 3 pairs for every date (n+1, n+2, n+3 pairs). It uses a 'matrix job' such that processing sets of interferograms for each year runs in parallel.

```
gh -R relativeorbit/fufiters workflow run fufiters_insar_pipeline.yml \
  -f burstId=012_023790_IW1  
```

#### Generate a set of pixel offsets for all years

```
gh -R relativeorbit/fufiters workflow run fufiters_offsets_pipeline.yml \
  -f burstId=012_023790_IW1  
```


## Configuration

* The workflow requires the following Actions secrets: 
  * AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY (for an IAM user that *only* has access to and S3 bucket)
  * EARTHDATA_USERNAME & EARTHDATA_PASSWORD (to download S1 Bursts from ASF DAAC)
  * ESA_USERNAME & ESA_PASSWORD (to download Sentinel-1 precise orbits from https://dataspace.copernicus.eu)


* Persistant COG and STAC outputs are stored in an AWS S3 Bucket (https://github.com/relativeorbit/pulumi-fufiters). 

## Ackowledgments
[University of Washington eScience Winter Incubator 2024](https://escience.washington.edu/incubator-24-glacial-lakes/)
