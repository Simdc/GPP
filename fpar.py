import numpy as np
import rasterio
import xarray as xr
import pandas as pd  # For date handling

def process_fpar_to_dataset(file1, file2, lat_factor=6, lon_factor=6):
    """
    Processes the two GeoTIFF files, calculates the monthly mean, performs coarsening using xarray,
    and returns an xarray.Dataset with time as a dimension.
    """
    # Extract time from the first file's name
    time = pd.Timestamp(file1.split("_")[-1][:8])  # Extracts 'YYYYMMDD' and converts to Timestamp

    with rasterio.open(file1) as src1, rasterio.open(file2) as src2:
        # Read FPAR (Band 1) and QC (Band 2) for both files
        data1_fpar = src1.read(1).astype(float)
        data1_qc = src1.read(2).astype(float)
        data2_fpar = src2.read(1).astype(float)
        data2_qc = src2.read(2).astype(float)

        # Replace fill values (65535) with NaN and scale FPAR values
        data1_fpar[data1_fpar == 65535] = np.nan
        data2_fpar[data2_fpar == 65535] = np.nan
        data1_fpar *= 0.001
        data2_fpar *= 0.001

        data1_qc[data1_qc == 65535] = np.nan
        data2_qc[data2_qc == 65535] = np.nan

        # Extract latitudes and longitudes from the raster metadata
        latitudes = np.linspace(src1.bounds.top, src1.bounds.bottom, src1.height)
        longitudes = np.linspace(src1.bounds.left, src1.bounds.right, src1.width)

    # Convert to xarray.DataArray
    fpar1_xr = xr.DataArray(data1_fpar, dims=["latitude", "longitude"], coords={"latitude": latitudes, "longitude": longitudes})
    fpar2_xr = xr.DataArray(data2_fpar, dims=["latitude", "longitude"], coords={"latitude": latitudes, "longitude": longitudes})
    qc1_xr = xr.DataArray(data1_qc, dims=["latitude", "longitude"], coords={"latitude": latitudes, "longitude": longitudes})
    qc2_xr = xr.DataArray(data2_qc, dims=["latitude", "longitude"], coords={"latitude": latitudes, "longitude": longitudes})

    # Calculate monthly means
    fpar_monthly_mean = xr.concat([fpar1_xr, fpar2_xr], dim="time").mean(dim="time", skipna=True)
    qc_monthly_mean = xr.concat([qc1_xr, qc2_xr], dim="time").mean(dim="time", skipna=True)

    # Coarsen the data
    fpar_monthly_mean_coarsened = fpar_monthly_mean.coarsen(latitude=lat_factor, longitude=lon_factor, boundary="trim").mean()
    qc_monthly_mean_coarsened = qc_monthly_mean.coarsen(latitude=lat_factor, longitude=lon_factor, boundary="trim").mean()

    # Create datasets
    fpar_dataset = xr.Dataset(
        {
            "fpar": (["time", "latitude", "longitude"], np.expand_dims(fpar_monthly_mean_coarsened.data, axis=0)),
        },
        coords={
            "time": [time],
            "latitude": fpar_monthly_mean_coarsened.latitude,
            "longitude": fpar_monthly_mean_coarsened.longitude,
        },
    )
    qc_dataset = xr.Dataset(
        {
            "qc": (["time", "latitude", "longitude"], np.expand_dims(qc_monthly_mean_coarsened.data, axis=0)),
        },
        coords={
            "time": [time],
            "latitude": qc_monthly_mean_coarsened.latitude,
            "longitude": qc_monthly_mean_coarsened.longitude,
        },
    )

    # Add attributes
    fpar_dataset["fpar"].attrs.update({
        "description": "GIMMS Monthly mean FPAR, sourced from PKU GIMMS NDVI",
        "units": "Fraction",
        "long_name": "Fraction of Photosynthetically Active Radiation",
    })
    qc_dataset["qc"].attrs.update({
        "description": "Monthly mean Quality Control (QC) data, inherited from PKU GIMMS NDVI",
        "long_name": "Quality Control (QC)",
        "notes": "Quality levels are 0, 1, 2, 3, in decreasing order of quality",
    })
    fpar_dataset["latitude"].attrs["units"] = "degrees_north"
    fpar_dataset["longitude"].attrs["units"] = "degrees_east"
    qc_dataset["latitude"].attrs["units"] = "degrees_north"
    qc_dataset["longitude"].attrs["units"] = "degrees_east"

    return fpar_dataset, qc_dataset

def run(prefix, start_year, end_year):
    all_fpar = []
    all_qc = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Construct file names
            file1 = f"{prefix}{year}{month:02d}01.tif"
            file2 = f"{prefix}{year}{month:02d}02.tif"

            try:
                # Process files to get datasets
                fpar_dataset, qc_dataset = process_fpar_to_dataset(file1, file2)

                all_fpar.append(fpar_dataset)
                all_qc.append(qc_dataset)
            except FileNotFoundError:
                print(f"Files not found for {file1} and {file2}. Skipping...")
                continue

    # Concatenate all datasets along the time dimension
    fpar_combined = xr.concat(all_fpar, dim="time")
    qc_combined = xr.concat(all_qc, dim="time")

    # Save to NetCDF files
    fpar_combined.to_netcdf("mod_FPAR_combined.nc")
    qc_combined.to_netcdf("mod_QC_combined.nc")

    print("NetCDF files saved: 'mod_FPAR_combined.nc' and 'mod_QC_combined.nc'")

# Example run
prefix = "GIMMS_FPAR4g_solely_"
run(prefix, 1982, 2015)
