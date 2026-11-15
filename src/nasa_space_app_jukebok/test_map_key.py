import pandas as pd

MAP_KEY = '972e6a6b134e0ef6a9366e372e7d6409'

debut = pd.to_datetime("2026-07-01")
bbox = "-5.5,41,10,51.5"

morceaux = []
for i in range(0, 30, 5):
    d = debut + pd.Timedelta(days=i)
    url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_SP/{bbox}/5/{d:%Y-%m-%d}'
    morceaux.append(pd.read_csv(url))

df_fra = pd.concat(morceaux, ignore_index=True)
df_fra = df_fra[df_fra.confidence >= 50].copy()

df_fra["aire_km2"] = df_fra["scan"] * df_fra["track"]
moyenne_feu = df_fra["frp"].mean()
espace_recouvert = df_fra["aire_km2"].sum()

print(len(df_fra), moyenne_feu, espace_recouvert)


print(df_fra)

par_jour = df_fra.groupby("acq_date").agg(
    nb_feux=("frp", "size"),
    frp_moyen=("frp", "mean"),
    surface_km2=("aire_km2", "sum"),
)
print(par_jour)
