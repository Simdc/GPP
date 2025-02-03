# **Footie commands (optional)**
To run this script on footie first execute the follwoing commands,

```bash
module avail
```
from the available anaconda modules choose one,
```bash
module anaconda/2023.09
```
After that based on what script you want to run install the important dependencies. In case you want to submit one of the scripts as a job save the following commands in a file, say run_gpp.slurm and run the file from cluster terminal,

```bash
#!/bin/bash
    
#SBATCH --job-name=test_job             # Name of the job
#SBATCH --output=test-%j.out            # Output file (%j is the job ID)
#SBATCH --error=test-%j.err             # Error file (%j is the job ID)
#SBATCH --workdir=/p/tmp/deepyama/GPP   # Replace with your working directory
#SBATCH --mem=10G                       # Request 5GB of RAM
#SBATCH --time=01:00:00                 # Set the job runtime to 60 minutes
#SBATCH --priority=high                 # Set the job priority to high

module load python/3.9                 # Load the Python module (adjust version as needed)
python gpp_complete_code.py                 # Run your script
```

# **GPP NetCDF Processing Pipeline**

## **Overview**
This script processes a NetCDF dataset (`VODCA2GPP_v1.nc`) containing Gross Primary Production (GPP) and uncertainty data. The script performs the following tasks:

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
python process_gpp.py
```
Ensure that `VODCA2GPP_v1.nc` is present in the same directory as the script.

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
- Reads and processes pixel coordinates from `grid_cal_uniq.txt`.
- Generates a PDF (`gpp_plots.pdf`) with GPP time-series plots at selected pixels.

## Usage
Run the script:
```bash
python gpp_check_v1.py
```

## Expected Outputs
- **gpp_plots.pdf**: A set of plots comparing old and new GPP datasets at different lat/lon locations.
- Printed logs indicating dataset processing steps and possible warnings.

## Notes
- Ensure the input files are present in the working directory.
- Modify `pixels_per_row` to adjust plot layout in the PDF.
- The script assumes nearest-neighbor selection for pixel extraction.

## Author
This script was developed for GPP dataset validation and analysis.

## **Contact**
For any questions or issues, feel free to reach out.

---
