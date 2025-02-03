import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cftime 
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.backends.backend_pdf import PdfPages

def convert_time_to_proleptic(ds, default_units="days since 1582-10-14 00:00:00"):
    """
    Converts the time variable in an xarray dataset to cftime format 
    using the proleptic_gregorian calendar if necessary.
    """
    if "time" not in ds:
        raise ValueError("Dataset does not contain a 'time' coordinate.")
    
    time_values = ds["time"].values

    # Check if time_values are already cftime
    if isinstance(time_values[0], cftime._cftime.DatetimeProlepticGregorian):
        # If already cftime, no need to convert
        print("Time values are already in cftime format.")
    else:
        # Get or set units
        time_units = ds["time"].attrs.get("units", default_units)

        # Convert time using cftime
        time_values = cftime.num2date(time_values, units=time_units, calendar="proleptic_gregorian")

    # Assign back to dataset
    ds["time"] = ("time", time_values)

    return ds

# Load datasets
ds_old = xr.open_dataset("/p/projects/lpjml/calibration/reference_data/FLUXCOMmet.GPP.360.720.1982.2010.30days.nc", decode_times=False)
ds_new = xr.open_dataset("/home/deepyama/GPP/VODCA2GPP_v1.nc", decode_times=False)


# Convert time to proleptic
ds_old = convert_time_to_proleptic(ds_old)
ds_new = convert_time_to_proleptic(ds_new)

# Resample the datasets (monthly mean)
gpp_old_monthly = ds_old["GPP"]
gpp_new_daily = ds_new["GPP"].resample(time="1MS").mean()

# Multiply new data by the number of days in the month
days_in_month_new = gpp_new_daily.time.dt.days_in_month
gpp_new_monthly_corrected = gpp_new_daily * days_in_month_new

# Get the common time range (min and max)
time_start = max(ds_old["time"].min(), ds_new["time"].min())
time_end = min(ds_old["time"].max(), ds_new["time"].max())

# Clip the data to the common time range
gpp_old_clipped = gpp_old_monthly.sel(time=slice(time_start, time_end))
gpp_new_clipped = gpp_new_monthly_corrected.sel(time=slice(time_start, time_end))

# Rename coordinates for consistency
gpp_new_clipped = gpp_new_clipped.rename({'lat': 'latitude', 'lon': 'longitude'})

# Ensure lat and lon are defined, for instance by using the latitudes and longitudes from the dataset
lat = gpp_old_clipped['latitude'].values  # Assuming latitude is a coordinate in your dataset
lon = gpp_old_clipped['longitude'].values  # Assuming longitude is a coordinate in your dataset

# Now, you can perform the selection using the 'nearest' method
gpp_old_pixel = gpp_old_clipped.sel(latitude=lat, longitude=lon, method="nearest")
gpp_new_pixel = gpp_new_clipped.sel(latitude=lat, longitude=lon, method="nearest")

import numpy as np

# Function to clean the lines before loading
def clean_data(file_path):
    # Read the file line by line
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Remove the header
    lines = lines[1:]

    # Clean rows and only keep those with exactly two columns
    cleaned_lines = []
    for line in lines:
        # Split the line into values
        columns = line.strip().split()
        
        # Only keep rows with exactly 2 columns
        if len(columns) == 2:
            cleaned_lines.append([float(columns[0]), float(columns[1])])

    # Convert cleaned lines into a numpy array
    return np.array(cleaned_lines)

# Load and clean the data
modified_pixels = clean_data("grid_cal_uniq.txt")

# Print the first few rows to verify the data
#print(modified_pixels)
data = []
for i in modified_pixels:
    
    x = i[0]
    y = i[1]
    data.append([x,y])

#data
# Set up the plot
fig, ax = plt.subplots(figsize=(10, 5), subplot_kw={'projection': ccrs.PlateCarree()})

## Add a map (world)
ax.coastlines()
ax.set_global()

# Plot the lat, lon points
for i in range(len(data)):
    ax.scatter(data[i][0], data[i][1], color='red', marker='o', s=10)

# Add title and legend
ax.set_title("World Map with Latitude/Longitude Points", fontsize=15)


# Show the plot
plt.show()

pixels = data

# Assume gpp_old_clipped and gpp_new_clipped are already loaded xarray datasets
# Assume pixels array contains latitude and longitude pairs

# Define the number of pixels per row for the plot grid
pixels_per_row = 5  # You can adjust this as needed

# Create a PDF file to save the plots
with PdfPages('gpp_plots.pdf') as pdf:
    # Iterate through each pixel in the pixels array
    for i, pixel in enumerate(pixels):
        lon, lat = pixel  # Extract latitude and longitude from the pixel list
        row = i // pixels_per_row  # Determine the row for the current pixel
        col = i % pixels_per_row   # Determine the column for the current pixel

        # Create a new figure for the current pixel's plot
        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

        # Extract GPP data for the current pixel (adjusting dimension names)
        gpp_old_pixel = gpp_old_clipped.sel(latitude=lat, longitude=lon, method="nearest")
        gpp_new_pixel = gpp_new_clipped.sel(latitude=lat, longitude=lon, method="nearest")

        # Convert time to datetime
        gpp_old_time = np.array(gpp_old_pixel.time.values, dtype='datetime64[ns]')
        gpp_new_time = np.array(gpp_new_pixel.time.values, dtype='datetime64[ns]')

        # Plot old GPP data in the left column
        axs[0].plot(gpp_old_time, gpp_old_pixel.values, label=f"Old ({lat:.2f}, {lon:.2f})", linestyle='--')
        axs[0].set_title(f"Old GPP Pixel {i+1} ({lat:.2f}, {lon:.2f})")
        axs[0].set_xlabel('Time')
        axs[0].set_ylabel('GPP (g C m^-2 month^-1)')
        axs[0].legend()

        # Plot new GPP data in the right column
        axs[1].plot(gpp_new_time, gpp_new_pixel.values, label=f"New ({lat:.2f}, {lon:.2f})", linestyle='-')
        axs[1].set_title(f"New GPP Pixel {i+1} ({lat:.2f}, {lon:.2f})")
        axs[1].set_xlabel('Time')
        axs[1].set_ylabel('GPP (g C m^-2 month^-1)')
        axs[1].legend()

        # Adjust layout to avoid overlap
        plt.tight_layout()

        # Save the current figure to the PDF
        pdf.savefig(fig)
        plt.close(fig)

print("Plots saved successfully to 'gpp_plots.pdf'.")
