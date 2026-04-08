
# Overview of processing design

## Reusable workflow hierarchy

| Workflow | Trigger | Calls | Details |
|---|---|---|---|
| **`insar_pair.yml`** | `workflow_dispatch` or `workflow_call` | — | Processes a single reference/secondary SLC pair for one burst; runs `hyp3_isce2`, uploads to S3 & GitHub Artifacts |
| **`insar_timeseries.yml`** | `workflow_dispatch` or `workflow_call` | `insar_pair` (matrix) | Searches ASF for all n+1/n+2/n+3 sequential pairs within a given year, then fans out to `insar_pair` in parallel |
| **`insar_pipeline.yml`** | `workflow_dispatch` | `insar_timeseries` (matrix) | Loops over years **2017–2024** in parallel, calling `insar_timeseries` for each year |

## Architecture diagram

```mermaid
flowchart LR
    P_IN[/"Inputs: burstId · polarization\nlooks · npairs"\]
    PIPELINE(["insar_pipeline.yml\nworkflow_dispatch"])
    MATRIX_YEAR["Matrix: years 2017-2024"]
    T_IN[/"Inputs: burstId · year · polarization\nlooks · npairs"\]
    TIMESERIES(["insar_timeseries.yml\nworkflow_call"])
    ASF["searchASF job\nn+1, n+2, n+3 burst pairs"]
    MATRIX_PAIR["Matrix: reference x secondary pairs"]
    PA[/"Inputs: reference · secondary\nburstId · polarization · looks"\]
    PAIR(["insar_pair.yml\nworkflow_call"])

    P_IN --> PIPELINE --> MATRIX_YEAR --> TIMESERIES --> ASF --> MATRIX_PAIR --> PAIR
    T_IN --> TIMESERIES
    PA --> PAIR

    style PIPELINE fill:#0075ca,color:#fff,stroke:#0075ca
    style TIMESERIES fill:#0075ca,color:#fff,stroke:#0075ca
    style PAIR fill:#0075ca,color:#fff,stroke:#0075ca
    style P_IN fill:#f0f0f0,color:#555,stroke:#ccc
    style T_IN fill:#f0f0f0,color:#555,stroke:#ccc
    style PA fill:#f0f0f0,color:#555,stroke:#ccc
```

```mermaid
flowchart TD
    PA[/"Inputs: reference · secondary\nburstId · polarization · looks"\]
    PAIR(["insar_pair.yml\nworkflow_call"])
    PB["Checkout relativeorbit/hyp3-isce2 @ fufiters branch"]
    PC["Setup pixi environment"]
    PD["Configure AWS Credentials"]
    PE["Cache DEM for Burst"]
    PF["Run hyp3_isce2: insar_tops_fufiters"]
    PG["Upload results to AWS S3"]
    PH["Upload GitHub Artifact"]

    PA --> PAIR --> PB --> PC --> PD --> PE --> PF
    PF --> PG
    PF --> PH

    style PAIR fill:#0075ca,color:#fff,stroke:#0075ca
    style PA fill:#f0f0f0,color:#555,stroke:#ccc
```
