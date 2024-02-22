# Comparision with hyp3-isce2

fufiters uses a custom workflow that is forked from ASF's hyp3-isce2 https://github.com/relativeorbit/hyp3-isce2 . The reason for using a fork is to quickly iterate on potentially breaking changes and not interfere with ASF's production workflows (https://github.com/ASFHyP3/hyp3-isce2/issues/170), though we intend to make upstream contributions where possible.


## Workflow deviations

### Full SLC inputs versus pre-preprocessed bursts
*hyp3-isce2 uses pre-processed SLC bursts as inputs, but those products are currently only available from June 2023 onwards, whereas the full SLC archive goes back to October 2014. ASF plans to pre-process the entire burst archive eventually, but we needed to process data going back to 2017:

> Single-burst datasets are currently available for data collected after June 9th, 2023. Creation of burst products for the entire SLC archive is expected to be complete by the end of June, 2024 (https://asf.alaska.edu/datasets/data-sets/derived-data-sets/sentinel-1-bursts/)

We therefore added a routine to extract a full burstId (`[Track]_[Burst]_[Subswath]`) from the original SLCs using ASF's burst extractor API (https://sentinel1-burst-documentation.asf.alaska.edu), allowing for processing any burst but requiring a change in workflow inputs. For example, the example hyp3-isce2 workflow:

```
python -m hyp3_isce2 ++process insar_tops_burst \
  S1_136231_IW2_20200604T022312_VV_7C85-BURST \
  S1_136231_IW2_20200616T022313_VV_5D11-BURST \
```

To process the same pair with fufiters the syntax becomes: 
```
python -m hyp3_isce2 ++process insar_tops_fufiters \
  S1A_IW_SLC__1SDV_20200604T022251_20200604T022318_032861_03CE65_7C85 \
  S1A_IW_SLC__1SDV_20200616T022252_20200616T022319_033036_03D3A3_5D11 \
  --burstId=064_136231_IW2
```

### Cloud-optimized outputs

Because we are generating a large dataset covering Nepal it is important to use Cloud-optimized outputs, so we add a workflow step to convert Geotiffs to Cloud-Optimized-Geotiffs (COGS) with Spatio-Temporal Asset Catalog (STAC) metadata

### Static Product IDs

hyp3-isce2 creates unique output folder names so that re-runing a workflow never overwrites pre-existing outputs. We wanted re-runing a workflow to overwrite ouputs and therefore remove this unique identifier suffix:
`S1_023790_IW1_20230621_20231218_VV_INT20_B6F2 -> S1_023790_IW1_20230621_20231218_VV_INT20`

### Compute Denseoffsets

Hyp3-isce2 disables runnning the denseOffsets step of the topsApp.py isce2 workflow. We needed to generate offset maps for long time spans in addition to short timespan interferograms, so we have an additional workflow to just compute offsets and skip interferogram creation, unwrapping, filtering, etc.


## Workflow deployment

ASF's Hyp3 uses AWS Batch to run a docker container of the standard hyp3-isce2 insar_tops_burst workflow (https://hyp3-docs.asf.alaska.edu/using/sdk/) This is a very convenient way to generate up to 1000 burst products per month if you have a NASA Earthdata login! However, we wanted to try deploying the workflow on GitHub Actions because we knew we would be exceding typical user quotas and also wanted to explore the merits of using GitHub actions versus a system like AWS Batch or Azure Batch. 

One drawback of this approach is that we are not running computations in the same datacenter as where the input Sentinel-1 SLCs are stored (AWS us-west-2), but because we are working with bursts instead of full-frame SLCs, download volumes are minimized. Alternatives include deploying a custom version of [Hyp3](https://github.com/ASFHyP3/hyp3) into our own AWS account or using cloud infrastructure management tools like prefect.io or coiled.io. 