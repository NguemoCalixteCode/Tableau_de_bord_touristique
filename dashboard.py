# --------------------------
# Dashboard Touristique Avancé Optimisé
# --------------------------
import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from geopy.distance import geodesic

# --------------------------
# Chargement des données avec cache
# --------------------------
@st.cache_data
def load_data():
    airbnb = pd.read_csv("data/airbnb/airbnb_all_cities_with_ratings.csv")
    restaurants = pd.read_csv("data/restaurants/restaurants_all_cities.csv")
    activities = pd.read_csv("data/activites/activites_all_cities.csv")
    return airbnb, restaurants, activities

airbnb, restaurants, activities = load_data()

# --------------------------
# Prétraitement
# --------------------------
airbnb['price'] = pd.to_numeric(airbnb['price'], errors='coerce')
airbnb = airbnb.dropna(subset=['latitude', 'longitude', 'price'])

price_map = {'€': 1, '€€': 2, '€€€': 3, '€€€€': 4}
restaurants['price_num'] = restaurants['price_range'].map(price_map)
restaurants = restaurants.dropna(subset=['latitude', 'longitude'])

activities['name'] = activities['name'].replace("Sans nom", "Activité sans nom")
activities = activities.dropna(subset=['lat', 'lon'])

# --------------------------
# Sidebar - Filtres
# --------------------------
st.sidebar.title("Filtres Voyageurs")

cities = sorted(airbnb['city'].unique())
selected_city = st.sidebar.selectbox("Choisir une ville", cities)

st.sidebar.subheader("Airbnb")
min_airbnb_rating = st.sidebar.slider("Note Airbnb minimale", 0.0, 5.0, 4.0)
room_type_filter = st.sidebar.multiselect(
    "Type de logement", airbnb['room_type'].unique(),
    default=airbnb['room_type'].unique()
)

st.sidebar.subheader("Restaurants")
cuisine_filter = st.sidebar.multiselect(
    "Type de cuisine", restaurants['cuisine_type'].unique(),
    default=restaurants['cuisine_type'].unique()
)
min_restaurant_rating = st.sidebar.slider("Note restaurants minimale", 0.0, 5.0, 4.0)

st.sidebar.subheader("Activités")
category_filter = st.sidebar.multiselect(
    "Catégorie d'activités", activities['category'].unique(),
    default=activities['category'].unique()
)

# --------------------------
# Filtrage avec cache
# --------------------------
@st.cache_data
def filter_data(city, airbnb_rating, room_types, rest_rating, cuisines, activity_categories):
    airbnb_f = airbnb[
        (airbnb['city'] == city) &
        (airbnb['rating_overall'] >= airbnb_rating) &
        (airbnb['room_type'].isin(room_types))
    ]
    restaurants_f = restaurants[
        (restaurants['city'] == city) &
        (restaurants['rating'] >= rest_rating) &
        (restaurants['cuisine_type'].isin(cuisines))
    ]
    activities_f = activities[
        (activities['city'] == city) &
        (activities['category'].isin(activity_categories))
    ]
    return airbnb_f, restaurants_f, activities_f

airbnb_filtered, restaurants_filtered, activities_filtered = filter_data(
    selected_city, min_airbnb_rating, room_type_filter,
    min_restaurant_rating, cuisine_filter, category_filter
)

# --------------------------
# KPIs
# --------------------------
st.title(f"Guide touristique interactif pour {selected_city}")

col1, col2, col3 = st.columns(3)
col1.metric("Airbnb disponibles", len(airbnb_filtered))
col2.metric("Restaurants disponibles", len(restaurants_filtered))
col3.metric("Activités disponibles", len(activities_filtered))

col1.metric("Note moyenne Airbnb", round(airbnb_filtered['rating_overall'].mean() if len(airbnb_filtered)>0 else 0,2))
col2.metric("Note moyenne Restaurants", round(restaurants_filtered['rating'].mean() if len(restaurants_filtered)>0 else 0,2))

# --------------------------
# Carte interactive avec limitation des points
# --------------------------
st.subheader("Carte interactive - Airbnb, Restaurants, Activités")
if len(airbnb_filtered) > 0:
    m = folium.Map(
        location=[airbnb_filtered['latitude'].mean(), airbnb_filtered['longitude'].mean()],
        zoom_start=13,
        tiles='CartoDB positron'
    )

    # Limiter à 50 points pour chaque catégorie pour accélérer le rendu
    max_points = 50
    for df, color, icon, name in [
        (airbnb_filtered.head(max_points), 'blue', 'home', 'Airbnb'),
        (restaurants_filtered.head(max_points), 'red', 'cutlery', 'Restaurants'),
        (activities_filtered.head(max_points), 'green', 'info-sign', 'Activités')
    ]:
        cluster = MarkerCluster(name=name).add_to(m)
        for _, row in df.iterrows():
            if name == 'Airbnb':
                popup = f"<b>{row['name']}</b><br>Note: {row['rating_overall']}<br>Prix: {row['price']}€<br><a href='{row['url']}' target='_blank'>Lien Airbnb</a>"
            elif name == 'Restaurants':
                popup = f"<b>{row['name']}</b><br>Note: {row['rating']}<br>Cuisine: {row['cuisine_type']}<br>Prix: {row['price_range']}<br><a href='{row['website']}' target='_blank'>Site web</a>"
            else:
                popup = f"<b>{row['name']}</b><br>Catégorie: {row['category']}"
            folium.Marker(
                location=[row['latitude'] if name!='Activités' else row['lat'], row['longitude'] if name!='Activités' else row['lon']],
                popup=popup,
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(cluster)

    folium.LayerControl().add_to(m)
    st_folium(m, width=800, height=500)
else:
    st.info("Pas de données Airbnb pour cette ville.")

# --------------------------
# Graphiques dynamiques avec palette joyeuse
# --------------------------
st.subheader("Graphiques et statistiques")
colors = px.colors.qualitative.T10

fig1 = px.histogram(
    restaurants_filtered,
    x='cuisine_type',
    color='cuisine_type',
    title=f"Répartition des types de cuisine à {selected_city}",
    color_discrete_sequence=colors
)
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.histogram(
    airbnb_filtered,
    x='room_type',
    color='room_type',
    title=f"Répartition des types de logement Airbnb à {selected_city}",
    color_discrete_sequence=colors
)
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.histogram(
    activities_filtered,
    x='category',
    color='category',
    title=f"Répartition des activités par catégorie à {selected_city}",
    color_discrete_sequence=colors
)
st.plotly_chart(fig3, use_container_width=True)

# --------------------------
# Tableaux interactifs
# --------------------------
st.subheader("Liste Airbnb recommandés")
st.dataframe(
    airbnb_filtered[['name','room_type','bedrooms','beds','person_capacity','price','rating_overall']].sort_values('rating_overall', ascending=False)
)

st.subheader("Liste Restaurants")
st.dataframe(
    restaurants_filtered[['name','cuisine_type','price_range','rating','total_ratings','address']].sort_values('rating', ascending=False)
)

st.subheader("Liste Activités")
st.dataframe(
    activities_filtered[['name','category','lat','lon']]
)

# --------------------------
# Top 5 Airbnb proches des activités/restaurants (vectorisé et cache)
# --------------------------
@st.cache_data
def compute_top_airbnb(airbnb_df, activities_df, restaurants_df, top_n=5):
    if len(airbnb_df)==0 or len(activities_df)==0 or len(restaurants_df)==0:
        return pd.DataFrame()
    
    airbnb_coords = airbnb_df[['latitude','longitude']].to_numpy()
    activity_coords = activities_df[['lat','lon']].to_numpy()
    restaurant_coords = restaurants_df[['latitude','longitude']].to_numpy()

    avg_distances = []
    for i, a in enumerate(airbnb_coords):
        d_act = np.mean(np.linalg.norm(a - activity_coords, axis=1))
        d_rest = np.mean(np.linalg.norm(a - restaurant_coords, axis=1))
        avg_distances.append(d_act + d_rest)
    
    airbnb_df = airbnb_df.copy()
    airbnb_df['avg_distance'] = avg_distances
    return airbnb_df.sort_values(by=['rating_overall','avg_distance'], ascending=[False,True]).head(top_n)

st.subheader("Top 5 Airbnb proches des activités et restaurants")
top_airbnb = compute_top_airbnb(airbnb_filtered, activities_filtered, restaurants_filtered)
if not top_airbnb.empty:
    st.dataframe(top_airbnb[['name','price','rating_overall','avg_distance']])
else:
    st.info("Pas assez de données pour calculer le top Airbnb.")
