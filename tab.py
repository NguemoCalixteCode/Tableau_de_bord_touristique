# --------------------------
# Dashboard Touristique Avancé - Version Optimisée et Colorée
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
# Chargement des données
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
# Filtrage des données
# --------------------------
airbnb_filtered = airbnb[
    (airbnb['city'] == selected_city) &
    (airbnb['rating_overall'] >= min_airbnb_rating) &
    (airbnb['room_type'].isin(room_type_filter))
].copy()

restaurants_filtered = restaurants[
    (restaurants['city'] == selected_city) &
    (restaurants['rating'] >= min_restaurant_rating) &
    (restaurants['cuisine_type'].isin(cuisine_filter))
].copy()

activities_filtered = activities[
    (activities['city'] == selected_city) &
    (activities['category'].isin(category_filter))
].copy()

# --------------------------
# Calcul distance Airbnb → activités/restaurants
# --------------------------
def compute_avg_distance(airbnb_row, activities_df, restaurants_df):
    distances = []
    for _, act in activities_df.iterrows():
        distances.append(geodesic((airbnb_row['latitude'], airbnb_row['longitude']),
                                  (act['lat'], act['lon'])).km)
    for _, res in restaurants_df.iterrows():
        distances.append(geodesic((airbnb_row['latitude'], airbnb_row['longitude']),
                                  (res['latitude'], res['longitude'])).km)
    return np.mean(distances) if distances else np.nan

# --------------------------
# KPIs
# --------------------------
st.title(f"🌞 Guide touristique interactif pour {selected_city}")

col1, col2, col3 = st.columns(3)
col1.metric("Airbnb disponibles", len(airbnb_filtered))
col2.metric("Restaurants disponibles", len(restaurants_filtered))
col3.metric("Activités disponibles", len(activities_filtered))

col1.metric("Note moyenne Airbnb", round(airbnb_filtered['rating_overall'].mean(), 2) if len(airbnb_filtered)>0 else "N/A")
col2.metric("Note moyenne Restaurants", round(restaurants_filtered['rating'].mean(), 2) if len(restaurants_filtered)>0 else "N/A")

# --------------------------
# Carte interactive
# --------------------------
st.subheader("🗺️ Carte interactive - Airbnb, Restaurants, Activités")
if len(airbnb_filtered) > 0:
    m = folium.Map(location=[airbnb_filtered['latitude'].mean(), airbnb_filtered['longitude'].mean()], zoom_start=13)
    
    # Airbnb - bleu joyeux
    airbnb_cluster = MarkerCluster(name='Airbnb').add_to(m)
    for _, row in airbnb_filtered.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"<b>{row['name']}</b><br>Note: {row['rating_overall']}<br>Prix: {row['price']}€<br>"
                  f"<a href='{row['url']}' target='_blank'>Lien Airbnb</a>",
            icon=folium.Icon(color='cadetblue', icon='home', prefix='fa')
        ).add_to(airbnb_cluster)

    # Restaurants - rouge-orange
    restaurant_cluster = MarkerCluster(name='Restaurants').add_to(m)
    for _, row in restaurants_filtered.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"<b>{row['name']}</b><br>Note: {row['rating']}<br>Cuisine: {row['cuisine_type']}<br>Prix: {row['price_range']}<br>"
                  f"<a href='{row['website']}' target='_blank'>Site web</a>",
            icon=folium.Icon(color='orange', icon='cutlery', prefix='fa')
        ).add_to(restaurant_cluster)

    # Activités - vert lumineux
    activity_cluster = MarkerCluster(name='Activités').add_to(m)
    for _, row in activities_filtered.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=f"<b>{row['name']}</b><br>Catégorie: {row['category']}",
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(activity_cluster)
    
    folium.LayerControl().add_to(m)
    st_folium(m, width=700, height=500)

# --------------------------
# Graphiques
# --------------------------
st.subheader("📊 Graphiques et statistiques")
color_palette = px.colors.qualitative.Bold  # Couleurs vives et harmonieuses

fig1 = px.histogram(restaurants_filtered, x='cuisine_type', color='cuisine_type', title="Répartition des types de cuisine", color_discrete_sequence=color_palette)
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.histogram(airbnb_filtered, x='room_type', color='room_type', title="Répartition des types de logement Airbnb", color_discrete_sequence=color_palette)
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.histogram(activities_filtered, x='category', color='category', title="Répartition des activités par catégorie", color_discrete_sequence=color_palette)
st.plotly_chart(fig3, use_container_width=True)

# --------------------------
# Tableaux interactifs
# --------------------------
st.subheader("🏡 Liste Airbnb recommandés")
st.dataframe(
    airbnb_filtered[['name', 'room_type', 'bedrooms', 'beds', 'person_capacity', 'price', 'rating_overall', 'url']]
    .sort_values(by='rating_overall', ascending=False)
)

st.subheader("🍽️ Liste Restaurants")
st.dataframe(
    restaurants_filtered[['name', 'cuisine_type', 'price_range', 'rating', 'total_ratings', 'address', 'website']]
    .sort_values(by='rating', ascending=False)
)

st.subheader("🎯 Liste Activités")
st.dataframe(
    activities_filtered[['name', 'category', 'lat', 'lon']]
)

# --------------------------
# Top 5 Airbnb proches des activités et restaurants
# --------------------------git init
st.subheader("🌟 Top 5 Airbnb proches des activités et restaurants")
if len(airbnb_filtered) > 0 and (len(activities_filtered) > 0 or len(restaurants_filtered) > 0):
    airbnb_filtered['avg_distance'] = airbnb_filtered.apply(
        lambda row: compute_avg_distance(row, activities_filtered, restaurants_filtered),
        axis=1
    )
    top_airbnb = airbnb_filtered.sort_values(by=['rating_overall', 'avg_distance'], ascending=[False, True]).head(5)
    st.dataframe(top_airbnb[['name', 'price', 'rating_overall', 'avg_distance', 'url']])
