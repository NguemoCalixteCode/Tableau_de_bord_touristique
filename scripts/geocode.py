import pandas as pd
import requests
from tqdm import tqdm
import time

# Charger la liste de villes
df = pd.read_csv("data/city_meta.csv")

def get_bbox(city, country="France"):
    """Retourne le bounding box (minlat, minlon, maxlat, maxlon) d'une ville"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": f"{city}, {country}", "format": "json", "limit": 1}
    headers = {"User-Agent": "DashboardVoyageCalixte/1.0"}
    r = requests.get(url, params=params, headers=headers)
    r.raise_for_status()
    res = r.json()
    if not res:
        return None
    bbox = res[0]["boundingbox"]
    return [float(bbox[0]), float(bbox[2]), float(bbox[1]), float(bbox[3])]

# Ajouter colonnes BBOX
bboxes = []
for city in tqdm(df["Ville"], desc="Géocodage"):
    try:
        bbox = get_bbox(city)
        bboxes.append(bbox)
        time.sleep(1)  # éviter le blocage de Nominatim
    except Exception as e:
        print(city, ":", e)
        bboxes.append([None]*4)

df[["min_lat","max_lat","min_lon","max_lon"]] = pd.DataFrame(bboxes)
df.to_csv("data/city_meta_bbox.csv", index=False)
print("✅ Bbox enregistrées dans data/city_meta_bbox.csv")
