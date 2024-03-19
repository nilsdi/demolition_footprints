# %%
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal, osr
from pathlib import Path
import math
from pyproj import Transformer


def pixel_to_geographic_coordinates(dataset, x, y):
    # Get the GeoTransform
    geotransform = dataset.GetGeoTransform()
    if geotransform is None:
        return None

    # Transform pixel coordinates to geographic coordinates
    x_geo = geotransform[0] + (x * geotransform[1]) + (y * geotransform[2])
    y_geo = geotransform[3] + (x * geotransform[4]) + (y * geotransform[5])

    # Get the projection from the dataset
    projection = dataset.GetProjection()
    srs = osr.SpatialReference(wkt=projection)
    unit = srs.GetLinearUnitsName()

    # If the projection is in meters, convert to degrees
    if unit == 'metre':
        transformer = Transformer.from_crs(srs.ExportToProj4(), 'EPSG:4326',
                                           always_xy=True)
        x_geo, y_geo = transformer.transform(x_geo, y_geo)

    return x_geo, y_geo


def display_rgb_geotiff_subset(file_path, x_start, y_start, width, height):
    # Open the GeoTIFF file
    dataset = gdal.Open(file_path)
    if dataset is None:
        print("Error: Unable to open the GeoTIFF file.")
        return

    # Read the subset of the RGB bands
    subset_rgb = dataset.ReadAsArray(x_start, y_start, width, height)

    # Plot the RGB subset using Matplotlib
    # Transpose the array to match Matplotlib's expectations for RGB images
    plt.imshow(np.transpose(subset_rgb, (1, 2, 0)))
    plt.colorbar(label='Pixel Intensity')
    plt.title("Subset of RGB GeoTIFF")

    # Set x-axis and y-axis ticks to show coordinates in degrees
    x_ticks = np.linspace(0, width, 5)
    y_ticks = np.linspace(0, height, 5)
    x_tick_labels = []
    y_tick_labels = []
    for x, y in zip(x_ticks, y_ticks):
        x_geo, y_geo = pixel_to_geographic_coordinates(dataset, x_start + x,
                                                       y_start + y)
        x_tick_labels.append('{:.4f}'.format(x_geo))
        y_tick_labels.append('{:.4f}'.format(y_geo))
    plt.xticks(x_ticks, labels=x_tick_labels, rotation=45)
    plt.yticks(y_ticks, labels=y_tick_labels)

    plt.xlabel("Longitude (degrees)")
    plt.ylabel("Latitude (degrees)")

    plt.show()


root_dir = str(Path(__file__).parents[2])
file_path = (root_dir + "/data/raw/orthophoto/res_0.3/trondheim_2019/" +
             "i_lzw_25/Eksport-nib.tif")
display_rgb_geotiff_subset(file_path, 77200, 9200, 1000, 1000)

# %% display size and resolution of the image

dataset = gdal.Open(file_path)
projection = dataset.GetProjection()
authority = projection.split('"')[1]
print(f"Projection: {authority}")
print(f"Size of the image: {dataset.RasterXSize} x {dataset.RasterYSize}")
geotransform = dataset.GetGeoTransform()
pixel_width = abs(geotransform[1])
pixel_height = abs(geotransform[5])

# Check units of the projection
projection = dataset.GetProjection()
srs = osr.SpatialReference(wkt=projection)
unit = srs.GetLinearUnitsName()

if unit != 'metre':
    # Constants
    EARTH_RADIUS = 6371 * 1000  # Earth's radius in meters
    LATITUDE = math.radians(63.43)  # Latitude of Trondheim, Norway in radians

    # Pixel resolution in degrees
    pixel_width_deg = pixel_width
    pixel_height_deg = pixel_height

    # Convert to radians
    pixel_width_rad = math.radians(pixel_width_deg)
    pixel_height_rad = math.radians(pixel_height_deg)

    # Convert to meters
    pixel_width = pixel_width_rad * EARTH_RADIUS * math.cos(LATITUDE)
    pixel_height = pixel_height_rad * EARTH_RADIUS

print(f"Pixel resolution: {pixel_width:.4f} x {pixel_height:.4f} meters")
# %%

file_path = (root_dir + "/data/temp/pretrain/images/" +
             "trondheim_2019_rect_image.tif")
display_rgb_geotiff_subset(file_path, 5000, 5000, 1000, 1000)
# %%
