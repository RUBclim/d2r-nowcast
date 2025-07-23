"""
Download the most recent ICON-D2 forecasts for Dortmund.

IMPORTANT
=========
For the script to work, it requires to have the following module installed:
    https://github.com/DeutscherWetterdienst/downloader    

Forecasts of ICON-D2 are performed 8 times a day for the forecast times
00, 03, 06, 09, 12, 15, 18, 21 UTC, with a forecast range of 48h.

More information are available here:
    https://www.dwd.de/DWD/forschung/nwv/fepub/icon_database_main.pdf
"""

import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import xarray as xr


def download_nwp(settings: dict) -> dict:
    """Download the most recent ICON-D2 forecasts for Dortmund."""

    model = settings["model"]
    grid = settings["grid"]
    fields = settings["fields"]
    start = settings["start"]
    end = settings["end"]
    step = settings["step"]
    model_timestamp = settings["timestamp"]

    lon_w, lon_e, lat_s, lat_n = settings["roi"]

    savedir = Path(settings["savedir"])
    savedir.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading the most recent {model.upper()} NWP for Dortmund")
    print("-" * 52)
    print(f"\nProcess started at: {datetime.now().strftime('%d/%m/%Y, %H:%M')}\n")

    data = {}

    for field in fields:

        with tempfile.TemporaryDirectory() as tempdir:
            try:
                subprocess.call(
                    [
                        "downloader",
                        "--model", model,
                        "--grid", grid,
                        "--single-level-fields", field,
                        "--min-time-step", str(start),
                        "--max-time-step", str(end),
                        "--time-step-interval", str(step),
                        "--timestamp", model_timestamp,
                        "--directory", tempdir,
                    ]
                )
            except subprocess.CalledProcessError as err:
                raise err

            fpaths = list(Path(tempdir).glob("*.grib2"))

            try:
                fpath = fpaths[0]
            except IndexError as exc:
                raise SystemExit("No files downloaded.") from exc

            try:
                model, _, _, _, timestamp, _, _, _, _ = fpath.stem.split("_")
            except ValueError:
                timestamp = fpath.stem.split("_")[4]
            run = timestamp[8:]
            date = timestamp[:8]
            savefile = savedir / timestamp / f"nwp-{date}-{run}-{field}.nc"
            savefile.parent.mkdir(parents=True, exist_ok=True)

            try:
                # NOTE:
                # cdo copy and mergetime handle an arbitrary amount of parameters
                # and can only be used together from version 2.3.0
                subprocess.call(
                    [
                        "cdo",
                        "-f", "nc",  # "copy",
                        "-seltime,00:00,01:00,02:00,03:00,04:00,05:00,06:00,07:00,08:00,09:00,10:00,11:00,12:00,13:00,14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00,23:00",
                        f"-sellonlatbox,{lon_w},{lon_e},{lat_s},{lat_n}",
                        "-mergetime", " ".join([str(fpath) for fpath in fpaths]),
                        str(savefile),
                    ]
                )
            except subprocess.CalledProcessError as err:
                raise err
            else:
                ds = xr.open_dataset(savefile)
                try:
                    data[field] = ds.squeeze(dim="height", drop=True)
                except KeyError:
                    data[field] = ds
            finally:
                print(
                    f"\n{field} field downloaded and saved to {savefile}.\n"
                )  # TODO: replace with logging

    nwps = {
        "date": date,
        "run": run,
        "dir": savefile.parent,
        "data": xr.merge(data.values(), compat="identical"),
    }

    return nwps


if __name__ == "__main__":
    sample_settings = {
        "model": "icon-d2",
        "grid": "regular-lat-lon",
        "fields": ("t_2m", "relhum_2m"),
        "step": 4,
        "start": 0,
        "end": 12,
        "timestamp": (datetime.utcnow() - timedelta(hours=15)).strftime("%Y-%m-%dT%H:%M:%S"),
        "roi": ("6.2", "7.8", "50.7", "51.7"),
        "savedir": Path.cwd(),
    }
    download_nwp(sample_settings)
