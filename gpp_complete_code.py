import os
import gc
import numpy as np
import xarray as xr
import pandas as pd
from tqdm import tqdm

# Load the dataset
file_path = "/p/projects/lpjml/calibration/reference_data/VODCA2GPP_wild2021_GPP_1988-2020.nc"
ds = xr.load_dataset(file_path, engine='netcdf4')

# Group the data by month and calculate the monthly mean
GPP_monthly_mean = (ds["GPP"]).resample(time='1MS').mean()
GPP_monthly = GPP_monthly_mean * GPP_monthly_mean['time'].dt.days_in_month

# Ensure the data starts from January and ends in December
start_date = GPP_monthly['time'].values[0]
end_date = GPP_monthly['time'].values[-1]

start_year, start_month = pd.Timestamp(start_date).year, pd.Timestamp(start_date).month
end_year, end_month = pd.Timestamp(end_date).year, pd.Timestamp(end_date).month

missing_start_dates = pd.date_range(
    start=f"{start_year}-01-01",
    end=f"{start_year}-{start_month - 1:02d}-01",
    freq="MS"
) if start_month != 1 else None

missing_end_dates = pd.date_range(
    start=f"{end_year}-{end_month + 1:02d}-01",
    end=f"{end_year}-12-01",
    freq="MS"
) if end_month != 12 else None

if missing_start_dates is not None and not missing_start_dates.empty:
    filler_start = xr.DataArray(
        data=np.full((len(missing_start_dates),) + GPP_monthly.shape[1:], np.nan),
        coords={
            "time": missing_start_dates,
            "lat": GPP_monthly["lat"],
            "lon": GPP_monthly["lon"]
        },
        dims=GPP_monthly.dims
    )
    GPP_monthly = xr.concat([filler_start, GPP_monthly], dim="time")

if missing_end_dates is not None and not missing_end_dates.empty:
    filler_end = xr.DataArray(
        data=np.full((len(missing_end_dates),) + GPP_monthly.shape[1:], np.nan),
        coords={
            "time": missing_end_dates,
            "lat": GPP_monthly["lat"],
            "lon": GPP_monthly["lon"]
        },
        dims=GPP_monthly.dims
    )
    GPP_monthly = xr.concat([GPP_monthly, filler_end], dim="time")

# Coarsen spatial resolution and save batches
pad = 2
num_batches = 4
batch_size = int(np.ceil(GPP_monthly.sizes["time"] / num_batches)) 
lat_factor, lon_factor = pad, pad
output_dir = "combined_output"
os.makedirs(output_dir, exist_ok=True)

coarsened_batches = []
for batch_idx in tqdm(range(num_batches), desc="Processing GPP batches"):
    start_idx = batch_idx * batch_size
    end_idx = min(start_idx + batch_size, GPP_monthly.sizes["time"])
    batch_data = GPP_monthly.isel(time=slice(start_idx, end_idx))

    coarsened_batch = batch_data.coarsen(lat=lat_factor, lon=lon_factor, boundary="trim").mean()
    coarsened_batch = coarsened_batch.to_dataset(name="GPP")

    coarsened_batch.attrs['units'] = 'g C m^-2 mon^-1'
    coarsened_batch.attrs['description'] = f"Coarsened batch from time {start_idx} to {end_idx}"

    coarsened_batches.append(coarsened_batch)
    del batch_data
    del coarsened_batch
    gc.collect()

combined_batch = xr.concat(coarsened_batches, dim='time')
combined_ds = xr.Dataset(
    {
        'GPP': combined_batch['GPP']
    },
    coords={
        'lat': combined_batch['lat'],
        'lon': combined_batch['lon'],
        'time': combined_batch['time'],
    },
)
combined_ds['lat'].attrs = GPP_monthly['lat'].attrs
combined_ds['lon'].attrs = GPP_monthly['lon'].attrs
combined_ds['time'].attrs = GPP_monthly['time'].attrs
combined_ds['GPP'].attrs['units'] = 'g C m^-2 mon^-1'
combined_filename = os.path.join(output_dir, 'combined_GPP.nc')
combined_ds.to_netcdf(combined_filename)
print(f"Saved combined GPP data: {combined_filename}")

# Process uncertainties
Uncertainties = ds["Uncertainties"]
coarsened_uncertainties = Uncertainties.coarsen(lat=lat_factor, lon=lon_factor, boundary="trim").mean()
coarsened_uncertainties = coarsened_uncertainties * 1000 / 12  # Update uncertainties by multiplying
coarsened_uncertainties.attrs['description'] = "Coarsened spatial uncertainties of the data (scaled)"
coarsened_uncertainties.attrs['units'] = 'g C m^-2 mon^-1'

uncertainties_dir = "coarsened_uncertainties"
os.makedirs(uncertainties_dir, exist_ok=True)
coarsened_uncertainties_ds = xr.Dataset(
    {
        "Uncertainties": coarsened_uncertainties
    },
    coords={
        "lat": coarsened_uncertainties['lat'],
        "lon": coarsened_uncertainties['lon']
    }
)
coarsened_uncertainties_ds['lat'].attrs = ds['lat'].attrs
coarsened_uncertainties_ds['lon'].attrs = ds['lon'].attrs
uncertainties_filename = os.path.join(uncertainties_dir, 'coarsened_uncertainties.nc')
coarsened_uncertainties_ds.to_netcdf(uncertainties_filename)
print(f"Saved coarsened Uncertainties data: {uncertainties_filename}")
