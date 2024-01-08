import os
import pyproj
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import matplotlib.pyplot as plt
import math

def get_exif_data(image):
    """Extract and return EXIF data from an image."""
    exif_data = {}
    exif = image._getexif()
    if exif is not None:
        for tag, value in exif.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data

def convert_to_degrees(value):
    """Converts the GPS coordinates stored as [degrees, minutes, seconds]."""
    d, m, s = value
    return d + m / 60.0 + s / 3600.0

def get_coordinates(exif_data):
    """Return latitude, longitude, and altitude from EXIF data."""
    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]
        
        lat = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef")
        altitude = gps_info.get("GPSAltitude")

        if lat and lon and lat_ref and lon_ref:
            latitude = convert_to_degrees(lat) * (-1 if lat_ref == "S" else 1)
            longitude = convert_to_degrees(lon) * (-1 if lon_ref == "W" else 1)

            if altitude:
                # Correct handling for IFDRational altitude
                altitude = altitude.numerator / float(altitude.denominator)
            else:
                altitude = 0
            
            return latitude, longitude, altitude

    return None, None, None

def to_utm(lat, lon):
    """Convert latitude and longitude to UTM coordinates."""
    # UTM zones are determined by longitude
    zone_number = math.floor((lon + 180) / 6) + 1

    proj_utm = pyproj.Proj(proj='utm', zone=zone_number, ellps='WGS84')
    utm_x, utm_y = proj_utm(lon, lat)
    return utm_x, utm_y

def plot_photo_locations(folder_path):
    utm_x_values = []
    utm_y_values = []
    altitudes = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(root, file)
                with Image.open(img_path) as img:
                    exif_data = get_exif_data(img)
                    lat, lon, alt = get_coordinates(exif_data)
                    if lat and lon:
                        utm_x, utm_y = to_utm(lat, lon)
                        utm_x_values.append(utm_x)
                        utm_y_values.append(utm_y)
                        altitudes.append(alt)

    # Plotting
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(60, 24))

    # Plot for UTM locations
    sc = ax1.scatter(utm_x_values, utm_y_values, c=altitudes, cmap='viridis')
    ax1.set_xlabel('UTM Easting (meters)')
    ax1.set_ylabel('UTM Northing (meters)')
    ax1.set_title('Photo Locations in UTM Coordinates')
    plt.colorbar(sc, ax=ax1, label='Altitude (meters)')

    # Setting grid lines at 1-meter intervals
    ax1.xaxis.set_major_locator(plt.MultipleLocator(1))
    ax1.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)

    # Plot for Z offsets
    ax2.scatter(range(len(altitudes)), altitudes, color='blue')
    ax2.set_xlabel('Photo Index')
    ax2.set_ylabel('Altitude (meters)')
    ax2.set_title('Z Offsets')

    # Saving plot to file with higher resolution
    plt.savefig(os.path.join(folder_path, "photo_locations_and_altitudes.png"), dpi=300)

    print(f"Plot saved as 'photo_locations_and_altitudes.png' in {folder_path}")

# Using the folder where this script is located
current_folder = os.path.dirname(os.path.realpath(__file__))
plot_photo_locations(current_folder)
