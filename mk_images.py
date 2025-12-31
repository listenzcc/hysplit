# %%
import itertools
import numpy as np
import pandas as pd
import imageio.v2 as imageio
import matplotlib.pyplot as plt

from PIL import Image
from pathlib import Path
from tqdm.auto import tqdm
from scipy.interpolate import griddata

# %%


def collect_and_generate_images(folder: Path):
    # Prepare folder
    folder = Path(folder)
    images_folder = folder / 'images'
    images_folder.mkdir(parents=True, exist_ok=True)

    # NW corner is (lat_min, lon_min)
    # SE corner is (lat_max, lon_max)

    # Find concentration.txt_xxx_yy files
    txt_files = sorted(folder.glob('concentration.txt_*'))
    dfs = []
    for f in tqdm(txt_files):
        csv = pd.read_csv(f, sep='\s+', skiprows=0)
        dfs.append(csv)

    table = pd.concat(dfs)
    table['m'] = table[table.columns[4]]
    table['m'] = table['m'] / table['m'].min()
    table['m'] = np.log10(table['m'])
    vmin,  vmax = table['m'].min(), table['m'].max()
    print(table)

    for day, hr in itertools.product(table['DAY'].unique(), table['HR'].unique()):
        df = table[(table['DAY'] == day) & (table['HR'] == hr)]
        if len(df) == 0:
            continue
        print(day, hr, len(df))
        plt.scatter(df['LON'], df['LAT'], c=df['m'], vmin=vmin, vmax=vmax)
        plt.xlim((table['LON'].min(), table['LON'].max()))
        plt.ylim((table['LAT'].min(), table['LAT'].max()))
        plt.savefig(folder / 'images' / f'{day}-{hr}.png')
        plt.close()

    return table


def collect_and_generate_images_1(folder: Path, lat_min, lat_max, lon_min, lon_max, grid_resolution=100):
    # Prepare folder
    folder = Path(folder)
    images_folder = folder / 'images'
    images_folder.mkdir(parents=True, exist_ok=True)

    # NW corner is (lat_min, lon_min)
    # SE corner is (lat_max, lon_max)

    # Find concentration.txt_xxx_yy files
    txt_files = sorted(folder.glob('concentration.txt_*'))

    # Convert the txt files into grayscale images
    image_files = []

    for f in txt_files:
        # Read data from file
        points_data = []
        conc_values = []

        with open(f, 'r') as file:
            for line in file:
                if line.startswith('DAY'):
                    continue  # Skip header
                parts = line.strip().split()
                if len(parts) >= 5:
                    lat = float(parts[2])
                    lon = float(parts[3])
                    concentration = float(parts[4])

                    # Check if point is within bounds
                    if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                        points_data.append([lat, lon])
                        conc_values.append(concentration)

        if len(points_data) < 3:  # Need at least 3 points for interpolation
            print(f"Not enough data points in {f.name} for interpolation")
            continue

        # Convert to numpy arrays
        points = np.array(points_data)
        values = np.array(conc_values)
        eps = np.min(values) / 1e3

        # Create regular grid for interpolation
        grid_lat = np.linspace(lat_min, lat_max, grid_resolution)
        grid_lon = np.linspace(lon_min, lon_max, grid_resolution)
        grid_lon_grid, grid_lat_grid = np.meshgrid(grid_lon, grid_lat)

        # Perform interpolation
        # Using linear interpolation, you can also try 'cubic' for smoother results
        try:
            grid_conc = griddata(points, values, (grid_lat_grid, grid_lon_grid),
                                 method='linear', fill_value=0)

            # If there are NaN values after interpolation, fill with 0
            grid_conc = np.nan_to_num(grid_conc, nan=0.0)
        except Exception as e:
            print(f"Interpolation failed for {f.name}: {e}")
            continue

        # Normalize for image display
        if np.max(grid_conc) > 0:
            # Log scale often works better for concentration data
            # Add small value to avoid log(0)
            conc_log = np.log10(grid_conc + eps)

            # Handle case where all values might be negative after log transform
            if np.max(conc_log) > np.min(conc_log):
                conc_norm = (conc_log - np.min(conc_log)) / \
                    (np.max(conc_log) - np.min(conc_log))
            else:
                conc_norm = np.zeros_like(conc_log)
        else:
            conc_norm = np.zeros_like(grid_conc)

        # Convert to 8-bit grayscale
        img_data = (conc_norm * 255).astype(np.uint8)

        # Create and save image
        img = Image.fromarray(img_data)

        # Optional: Resize if needed
        # img = img.resize((500, 500), Image.Resampling.LANCZOS)

        img_filename = images_folder / f"{f.name}.png"
        img.save(img_filename)
        image_files.append(img_filename)

        print(f"Generated image: {img_filename}")

    # Generate gif if we have multiple images
    if len(image_files) > 1:
        gif_filename = folder / 'concentration_animation.gif'

        # Read all images
        images = []
        for img_file in image_files:
            images.append(imageio.imread(img_file))

        # Save as GIF
        # 0.5 seconds per frame
        imageio.mimsave(gif_filename, images, duration=0.5)
        print(f"Generated GIF: {gif_filename}")

    return len(image_files)


# %%
if __name__ == '__main__':
    kwargs = dict(
        lat_min=30,
        lat_max=33,
        lon_min=115,
        lon_max=130
    )

    # collect_and_generate_images(
    #     './hysplit_simulation/1767078539.772455-bc5c1b4e-e770-45b5-945f-5a0f9fb46434', **kwargs)

    collect_and_generate_images(
        './hysplit_simulation/1767078539.772455-bc5c1b4e-e770-45b5-945f-5a0f9fb46434')
