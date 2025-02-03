# README: GPP Data Processing and Analysis

## Overview
This project processes and analyzes Gross Primary Production (GPP) data from NetCDF files using Python. It includes spatial coarsening, uncertainty computation, and visualization.

## Installation
Ensure you have the required dependencies installed:
```bash
pip install numpy pandas xarray tqdm netCDF4 matplotlib cartopy cftime
```

## GPP Data Processing
The script performs the following steps:
1. **Load the NetCDF file** (`VODCA2GPP_v1.nc`).
2. **Compute Monthly Mean GPP**:
   - Resample data by month.
   - Multiply by the number of days per month to get total monthly values.
3. **Ensure Data Completeness**:
   - Adds missing months to ensure a complete year (January to December).
4. **Coarsen Spatial Resolution**:
   - Uses a `pad` factor to reduce resolution.
5. **Batch Processing**:
   - Divides the dataset into `num_batches` to manage memory usage.
   - Saves coarsened results to NetCDF.
6. **Uncertainty Computation**:
   - Computes and scales uncertainty values.

## How to Calculate `pad`
The `pad` value determines the coarsening factor for latitude and longitude.
- Choose a suitable factor based on the dataset's resolution.
- Example: If original data has `0.1°` resolution and you need `0.5°`, set `pad = 5`.

## Visualization & Validation (`gpp_check_v1.py`)
The second script (`gpp_check_v1.py`) performs the following:
1. **Loads datasets** (`FLUXCOMmet.GPP.360.720.1982.2010.30days.nc` and `VODCA2GPP_v1.nc`).
2. **Converts time to `proleptic_gregorian` format**.
3. **Resamples the new dataset to monthly values**.
4. **Clips data to common time ranges**.
5. **Extracts GPP values at selected pixels**.
6. **Plots GPP time series comparisons** and saves to `gpp_plots.pdf`.

### Example Code from `gpp_check_v1.py`
```python
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cftime
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.backends.backend_pdf import PdfPages

# Function to convert time format
def convert_time_to_proleptic(ds, default_units="days since 1582-10-14 00:00:00"):
    if "time" not in ds:
        raise ValueError("Dataset does not contain a 'time' coordinate.")
    
    time_values = ds["time"].values

    if isinstance(time_values[0], cftime._cftime.DatetimeProlepticGregorian):
        print("Time values are already in cftime format.")
    else:
        time_units = ds["time"].attrs.get("units", default_units)
        time_values = cftime.num2date(time_values, units=time_units, calendar="proleptic_gregorian")

    ds["time"] = ("time", time_values)
    return ds
```

## Output Files
- `combined_GPP.nc`: Coarsened GPP dataset.
- `coarsened_uncertainties.nc`: Coarsened uncertainty data.
- `gpp_plots.pdf`: Visualization of old vs. new GPP data.

## Usage
Run the main processing script:
```bash
python gpp_processing.py
```
For validation and visualization:
```bash
python gpp_check_v1.py
```

## License
MIT License.

## Contact
For questions, contact the project maintainer.

