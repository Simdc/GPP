# **Footie commands (optional)**
To run this script on footie first execute the follwoing commands,

```bash
module avail
```
from the available anaconda modules choose one,
```bash
module load anaconda/2023.09
```
After that based on what script you want to run install the important dependencies.

# **GPP NetCDF Processing Pipeline**

## **Overview**
This script (gpp_complete_code.py) processes a NetCDF dataset (`VODCA2GPP_v1.nc`) containing Gross Primary Production (GPP) and uncertainty data. The script performs the following tasks:

1. **Load the dataset** using `xarray`.
2. **Aggregate the data monthly** by computing the mean and adjusting for the number of days in each month.
3. **Ensure full-year coverage** by filling missing months with NaNs if the dataset does not start in January or end in December.
4. **Coarsen spatial resolution** by averaging over spatial regions.
5. **Batch process the data** to avoid memory overload, saving processed data incrementally.
6. **Save the combined GPP dataset** as a NetCDF file.
7. **Process uncertainty data**, apply coarsening, scale it, and save it separately.

---

## **Installation**
Ensure you have the required Python libraries installed before running the script:
```bash
pip install numpy pandas xarray netCDF4 h5netcdf tqdm
```

### **Required Modules**
- `os`: Handles file system operations.
- `gc`: Manages garbage collection to free memory.
- `numpy (np)`: Used for numerical computations.
- `xarray (xr)`: Used for handling multidimensional NetCDF data.
- `pandas (pd)`: Used for date/time manipulation.
- `tqdm`: Provides a progress bar for batch processing.

---

## **Usage**
To run the script, simply execute:
```bash
python gpp_complete_code.py
```
Ensure that `VODCA2GPP_v1.nc`(the data.nc file to process) is present in the same directory as the script. Also modify the pad value(coarsening factor) if necessary. More on pad value is mentioned below. The 1000/12 factor used for unit conversion under point 6., must be also be changed if you do not want to convert your data from kg/yr to g/mon. 

---

## **Step-by-Step Processing**

### **1. Load the NetCDF Dataset**
The dataset is loaded using:
```python
file_path = "/home/deepyama/GPP/VODCA2GPP_v1.nc"
ds = xr.load_dataset(file_path, engine='netcdf4')
```

### **2. Compute Monthly Mean GPP**
The script resamples the data to a monthly mean and adjusts for different month lengths:
```python
GPP_monthly_mean = (ds["GPP"]).resample(time='1MS').mean()
GPP_monthly = GPP_monthly_mean * GPP_monthly_mean['time'].dt.days_in_month
```

### **3. Ensure Full-Year Coverage**
If the dataset does not start in January or end in December, missing months are filled with NaNs.

### **4. Batch Processing and Spatial Coarsening**
To manage memory efficiently, the data is divided into batches:
```python
pad = 2  # Define coarsening factor
num_batches = 4
batch_size = int(np.ceil(GPP_monthly.sizes["time"] / num_batches))
lat_factor, lon_factor = pad, pad
```
Each batch undergoes spatial coarsening:
```python
coarsened_batch = batch_data.coarsen(lat=lat_factor, lon=lon_factor, boundary="trim").mean()
```

### **5. Save the Processed Data**
The processed GPP data is saved in `combined_output/combined_GPP.nc`.

### **6. Process Uncertainty Data**
Uncertainty values are coarsened and scaled:
```python
coarsened_uncertainties = Uncertainties.coarsen(lat=lat_factor, lon=lon_factor, boundary="trim").mean()
coarsened_uncertainties = coarsened_uncertainties * 1000 / 12
```
The resulting data is saved in `coarsened_uncertainties/coarsened_uncertainties.nc`.

It is to note that the 1000/12 factor converts the kg/yr to g/mon. This factor must be modified based on units of the original dataset.

---

## **How to Calculate `pad` (Coarsening Factor)**
`pad` determines how many grid points are averaged when coarsening spatial resolution. The optimal value depends on the resolution of the dataset and the desired level of downscaling.

To determine `pad`:
1. **Check the dataset resolution** (e.g., if the dataset has a spatial resolution of `0.1° × 0.1°`, meaning 10 km per grid cell).
2. **Decide the target resolution** (e.g., `0.2° × 0.2°` means averaging `2 × 2` grid cells → `pad = 2`).
3. **Set `pad` accordingly**: Higher values increase spatial aggregation.

For example, if the dataset is in `0.05° × 0.05°` resolution and you want `0.25° × 0.25°`, then:
```python
pad = 5  # Since 0.25 / 0.05 = 5
```

---

## **Output Files**
- **`combined_GPP.nc`**: Coarsened monthly GPP dataset.
- **`coarsened_uncertainties.nc`**: Coarsened uncertainties dataset.

---

# GPP Data Validation and Visualization

## Overview
This script (`gpp_check_v1.py`) is designed to validate and compare Gross Primary Productivity (GPP) datasets by converting time formats, resampling data, and visualizing differences using latitude-longitude points. It generates a PDF containing time-series plots of selected pixels.

## Requirements
Ensure you have the following Python libraries installed:
```bash
pip install xarray numpy matplotlib cftime cartopy netcdf4 h5netcdf
```
### **Locations of the NetCDF Datasets**
The dataset is loaded using:
```bash
ds_old = xr.open_dataset("/p/projects/lpjml/calibration/reference_data/FLUXCOMmet.GPP.360.720.1982.2010.30days.nc", decode_times=False)
ds_new = xr.open_dataset("/home/deepyama/GPP/VODCA2GPP_v1.nc", decode_times=False)
```


## Features
- Converts time formats to `proleptic_gregorian` if necessary.
- Loads and processes two datasets: `FLUXCOMmet.GPP.360.720.1982.2010.30days.nc` and `VODCA2GPP_v1.nc`.
- Resamples daily data to monthly means and corrects for varying month lengths.
- Selects common time periods for accurate comparison.
- Reads and processes pixel coordinates from `grid_cal_uniq.txt`(/p/projects/lpjml/calibration/input/tropical_allsoils/grid_cal_uniq.txt).
- Generates a PDF (`gpp_plots.pdf`) with GPP time-series plots at selected pixels.

## Usage
Run the script:
```bash
python gpp_check_v1.py
```
Make sure to correctly modify the location of the datasets to be compared.
## Expected Outputs
- **gpp_plots.pdf**: A set of plots comparing old and new GPP datasets at different lat/lon locations.
- Printed logs indicating dataset processing steps and possible warnings.

## Notes
- Ensure the input files are present in the working directory.
- Modify `pixels_per_row` to adjust plot layout in the PDF.
- The script assumes nearest-neighbor selection for pixel extraction.

Here's the updated README that includes the installation instructions for the necessary dependencies:

---

# FPAR data processing

This Python script(fpar.py) processes two GeoTIFF files containing FPAR (Fraction of Photosynthetically Active Radiation) and QC (Quality Control) data, calculates the monthly mean, coarsens the data using `xarray`, and saves the results as NetCDF files.

## Table of Contents

- [Dependencies](#dependencies)
- [Description](#description)
- [Code Overview](#code-overview)
- [Installation](#installation)
- [Usage](#usage)

## Dependencies

Before running the script, ensure the following Python libraries are installed:

- `rasterio`
- `netCDF4`
- `matplotlib`
- `xarray`

## Installation

You can install the necessary dependencies using `pip` by running the following command:

```bash
pip install rasterio netCDF4 matplotlib xarray
```

Alternatively, you can create a `requirements.txt` file with the following contents:

```
rasterio
netCDF4
matplotlib
xarray
```

Then, install the dependencies using:

```bash
pip install -r requirements.txt
```

## Description

The script processes monthly data from two GeoTIFF files, one for the first half of the month and another for the second half. The primary objective is to:

1. Read the FPAR and QC data from the files.
2. Replace fill values with `NaN`.
3. Scale the FPAR values.
4. Calculate the monthly mean of FPAR and QC data.
5. Coarsen the data using latitude and longitude factors.
6. Save the results as NetCDF files for further use.

The output consists of two NetCDF files:
- One for FPAR data (`.nc`)
- One for QC data (`.nc`)

## Code Overview

### Main Function: `process_fpar_to_netcdf`

This function processes two GeoTIFF files to compute the monthly mean FPAR and QC data, coarsens it, and saves the results as NetCDF files.

#### Parameters:
- `file1`, `file2`: Path to the first and second GeoTIFF files.
- `output_fpar_filename`, `output_qc_filename`: Names for the output NetCDF files.
- `lat_factor`, `lon_factor`: Coarsening factors for latitude and longitude (default values are `6`).

#### Coarsening Factor:

The coarsening factor controls how much the spatial resolution of the data is reduced by averaging neighboring cells. It is calculated as the ratio of the original resolution to the desired resolution:

$Coarsening Factor=Original Resolution/Desired Resolution$

For example, if the original grid has a resolution of 12° x 12° and you want to coarsen it to 2° x 2°, the coarsening factor would be 6 for both latitude and longitude. This means every 2x2 block of cells is averaged into a single coarsened cell.

### Helper Function: `save_to_netcdf`

This function saves the processed data into NetCDF files with proper attributes.

#### Parameters:
- `filename`: Path to the output NetCDF file.
- `data`: Data to be saved.
- `var_name`: Variable name in the NetCDF file.
- `description`: Description of the variable.
- `units`: Units for the variable.

### Function: `run`

The `run` function processes multiple years of data by constructing file names for each month between the specified start and end years. It calls `process_fpar_to_netcdf` to process the files and generate the output.

#### Parameters:
- `prefix`: Prefix for the input GeoTIFF files. Also mention the the location of the files along with it, for example: prefix = "/path/to/your/files/GIMMS_FPAR4g_".
- `start_year`, `end_year`: The range of years for processing.

## Usage

1. Make sure all dependencies are installed.
2. Modify the `prefix`, `start_year`, `coarsening factor` and `end_year` variables to match your data.
3. Call the `run` function to process the data.
4. In our case the fill_value and scaling factor was mentioned based on the dataset, for other datasets make sure to modify them, the code snippet(from function process_fpar_to_netcdf) below must be modified,

```python
data1_fpar[data1_fpar == 65535] = np.nan
data2_fpar[data2_fpar == 65535] = np.nan
data1_fpar *= 0.001
data2_fpar *= 0.001

data1_qc[data1_qc == 65535] = np.nan
data2_qc[data2_qc == 65535] = np.nan
```

Example:
In our case the input file start with prefix "GIMMS_FPAR4g_" thus we pass it as prefix. If the input files and the code are not in same directory then please also add the PATH with the prefix. In that case prefix looks like, prefix = "C:\home\documents\data\GIMMS_FPAR4g_". Also, correct start year and end year must be mentioned with the function-run.

```python
prefix = "GIMMS_FPAR4g_"
run(prefix, 1982, 2022)
```

This will process the data for the years 1982 to 2022 and save the output as NetCDF files for each month.

---

This README will provide users with clear instructions on how to install the necessary dependencies and use the script effectively.
## Author
This scripts are being developed for data processing pipeline on FOOTE. 
## **Contact**
For any questions or issues, feel free to reach out to deepyama@pik-potsdam.de .

---
