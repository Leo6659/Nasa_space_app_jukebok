import matplotlib.pyplot as plt
import pandas as pd
from owslib.wms import WebMapService
import os

MAP_KEY = "<Enter your key here>"


da = pd.read_csv(f"https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{MAP_KEY}/all")
# Zone dézoomée (avant : -1.7, 44.3, -0.4, 45.2)
ouest, sud, est, nord = -2.0, 44.1, -0.1, 45.4
bbox = f"{ouest},{sud},{est},{nord}"

debut = pd.to_datetime("2026-07-20")
fin = "2026-08-03"


plan = []
for sat in ["VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP"]:
  plan += [
    (f"{sat}_SP", "2026-07-20", 5),
    (f"{sat}_SP", "2026-07-25", 5),
    (f"{sat}_SP", "2026-07-30", 2),
    (f"{sat}_NRT", "2026-08-01", 3),
  ]

morceaux = []
for source, date_debut, nb_jours in plan:
  url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{source}/{bbox}/{nb_jours}/{date_debut}"
  try:
    m = pd.read_csv(url)
    m["source"] = source
    morceaux.append(m)
  except Exception as e:
    print("échec", source, date_debut, e)

df_fra = pd.concat(morceaux, ignore_index=True)

df_fra = df_fra[df_fra.acq_date.between("2026-07-20", fin) & df_fra.confidence.isin(["n", "h"])].copy()

df_fra["aire_km2"] = df_fra["scan"] * df_fra["track"]
moyenne_feu = df_fra["frp"].mean()
espace_recouvert = df_fra["aire_km2"].sum()

print(len(df_fra), moyenne_feu, espace_recouvert)
print(df_fra.groupby("source").size())
print(df_fra.groupby(["acq_date", "satellite"]).size().unstack(fill_value=0))
print(df_fra)

par_jour = df_fra.groupby("acq_date").agg(
    nb_feux=("frp", "size"),
    frp_moyen=("frp", "mean"),
    surface_km2=("aire_km2", "sum"),
)
print(par_jour)

wms = WebMapService(
    "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?",
    version="1.1.1",
)
img = wms.getmap(
    layers=["MODIS_Terra_CorrectedReflectance_TrueColor"],
    srs="epsg:4326",
    bbox=(ouest, sud, est, nord),
    size=(1460, 1000),
    format="image/png",
    time="2026-07-20",
)
open("fond.png", "wb").write(img.read())
fond = plt.imread("fond.png")

# --- Une image par jour ---
os.makedirs("frames", exist_ok=True)
jours = pd.date_range("2026-07-20", fin).strftime("%Y-%m-%d")

for i, jour in enumerate(jours):
    feux_jour = df_fra[df_fra.acq_date == jour]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(fond, extent=[ouest, est, sud, nord], origin="upper")
    ax.scatter(
        feux_jour.longitude,
        feux_jour.latitude,
        c="red",
        s=40,
        label=f"{len(feux_jour)} détections",
    )
    ax.set_xlim(ouest, est)
    ax.set_ylim(sud, nord)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Détections thermiques - {jour}")
    ax.legend(loc="upper left")

    fig.savefig(f"frames/{i:03d}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
