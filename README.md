# Fufiters

[![Test Workflow](https://github.com/relativeorbit/fufiters/actions/workflows/nightly_test.yml/badge.svg)](https://github.com/relativeorbit/fufiters/actions/workflows/nightly_test.yml)

[![DOI](https://zenodo.org/badge/742564947.svg)](https://doi.org/10.5281/zenodo.15166765)

A combined InSAR, pixel-offsets workflow for measuring elevation change in Nepal using [Sentinel-1 Synthethic Aperture Radar bursts](https://asf.alaska.edu/datasets/data-sets/derived-data-sets/sentinel-1-bursts/)

See the following manuscript in The Cryosphere Journal for a detailed application of this software: https://egusphere.copernicus.org/preprints/2024/egusphere-2024-3196/

## Design

Run a modified version of [hyp3-isce2](https://github.com/ASFHyP3/hyp3-isce2) to generate an inventory of inteferograms and pixel offset maps for a given Sentinel-1 burst. Workflows are written using Python scripts and GitHub Actions for concurrent batch processing on Microsoft Azure.

[Resuable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows) are composed to run processing of a single image pair, to processing all pairs over all available years in parallel (Sentinel-1 acquisitions start in October 2014).

At a minimum you need to select a Sentinel-1 Burst. You can search for Burst IDs using [NASA Earthdata Search](https://search.earthdata.nasa.gov/search/granules?p=C2450786986-ASF&pg[0][v]=f&pg[0][id]=*IW*&pg[0][gsk]=-start_date&g=G2453394254-ASF&q=burst&sb[0]=80.82422%2C26.11576%2C87.97852%2C30.47298&tl=1708033475.92!3!!&lat=25.619422925906335&long=78.22265625&zoom=5

## Instructions

Install the [GitHub actions CLI](https://cli.github.com) in order to easily run workflows from the command line. Alternatively you can manually run workflows from the 'Actions' repository tab.

Note: you must be a member of this GitHub organization to run these workflows, or you can fork this repository and add your own secrets (see below).

#### Generate a single burst interferogram:

Use the full SLC names and specify the full burstId (`[Track]_[Burst]_[Subswath]`) that you want to process:

```
gh -R relativeorbit/fufiters workflow run insar_pair.yml \
  -f reference=S1A_IW_SLC__1SDV_20190101T121401_20190101T121429_025284_02CBEB_65D7 \
  -f secondary=S1A_IW_SLC__1SDV_20190113T121401_20190113T121429_025459_02D234_3311 \
  -f burstId=012_023790_IW1
```
Note: to select SLC names you can use https://search.asf.alaska.edu or use ASF's Python Client https://github.com/asfadmin/Discovery-asf_search

Optional inputs for all workflows:
```
nlooks=5x1 [20x4, 10x2]
polarization=VV [HH]
```

##### Run workflow locally (only works on Linux/MacOS Intel due to ISCE2 dependency)

You must first install a specific branch of `hyp3-isce2`, we recommend using [pixi](https://pixi.sh/latest/installation/) to setup a reproducible (locked) environment:

```bash
git clone https://github.com/relativeorbit/hyp3-isce2.git
pixi shell --frozen

cd /tmp
python -m hyp3_isce2 ++process insar_tops_fufiters \
  S1A_IW_SLC__1SDV_20190101T121401_20190101T121429_025284_02CBEB_65D7 \
  S1A_IW_SLC__1SDV_20190113T121401_20190113T121429_025459_02D234_3311 \
  --burstId 012_023790_IW1 \
  --looks 20x4 \
  --apply-water-mask False
```

#### Generate a set of interferograms for a specific year

This workflow will do the search automatically and create 3 pairs for every acquisition date in a year (n+1, n+2, n+3 pairs).
```bash
gh -R relativeorbit/fufiters workflow run insar_timeseries.yml \
  -f year=2023 \
  -f burstId=012_023790_IW1
```

#### Generate a set of interferograms for all years


This workflow will do the search automatically and create 3 pairs for every date (n+1, n+2, n+3 pairs). It uses a 'matrix job' such that processing sets of interferograms for each year runs in parallel.

```bash
gh -R relativeorbit/fufiters workflow run insar_pipeline.yml \
  -f burstId=012_023790_IW1
```

#### Generate a set of pixel offsets for all years

```bash
gh -R relativeorbit/fufiters workflow run offsets_pipeline.yml \
  -f burstId=012_023790_IW1
```


#### Download artifacts

Note this particular workflow was run twice

```bash
gh -R relativeorbit/fufiters run list -w insar_pipeline.yml

STATUS  TITLE                     WORKFLOW        BRANCH  EVENT              ID          ELAPSED   AGE
✓       121_258662_IW2 VV 5x1 3   InSAR_Pipeline  main    workflow_dispatch  8072975855  23m26s    about 15 hours ago
✓       121_258661_IW2 VV 5x1 2   InSAR_Pipeline  main    workflow_dispatch  8055416864  1h29m41s  about 1 day ago
```

```bash
gh -R relativeorbit/fufiters run view 8072975855
```

```bash
# Download interferograms for a specific date
gh -R relativeorbit/fufiters run download 8072975855 --dir /tmp/121_258662_IW2 --pattern "*20190813*"

# Specific artifact
gh -R relativeorbit/fufiters run download 8072975855 --dir /tmp/121_258662_IW2 --name "20190720_20190813"

# All artifacts (may take a while!)
gh -R relativeorbit/fufiters run download 8072975855 --dir /tmp/121_258662_IW2
```


## Configuration

* The workflow requires the following Actions secrets:
  * `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` (for an IAM user that *only* has access to and S3 bucket)
  * `EARTHDATA_USERNAME` & `EARTHDATA_PASSWORD` (to download S1 Bursts from ASF DAAC https://urs.earthdata.nasa.gov)
  * `ESA_USERNAME` & `ESA_PASSWORD` (to download Sentinel-1 precise orbits from https://dataspace.copernicus.eu)


* Persistant COG outputs are stored in an AWS S3 Bucket (configured here https://github.com/relativeorbit/pulumi-fufiters).

## Acknowledgments
[University of Washington eScience Winter Incubator 2024](https://escience.washington.edu/incubator-24-glacial-lakes/)
