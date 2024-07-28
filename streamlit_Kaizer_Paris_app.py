### Importation
import pandas as pd
import geopandas as gpd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(
    page_title="Comptage cyclable à Paris",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour charger les données
def load_data():
    try:
        Paris_geojson = 'Données/arrondissements.geojson'
        gdf = gpd.read_file(Paris_geojson)

        Velo_CSV = 'Données/Velo_Paris_new.csv'
        Paris_velo = pd.read_csv(Velo_CSV, sep=',')

        Paris_velo['l_ar'] = Paris_velo['l_ar'].astype(str)
        gdf['l_ar'] = gdf['l_ar'].astype(str)

        gdf = gdf.to_crs(epsg=4326)
        gdf['centroid'] = gdf.geometry.centroid
        gdf['Code_Lat'] = gdf['centroid'].y
        gdf['Code_Long'] = gdf['centroid'].x

        gdf = gdf.merge(Paris_velo, on='l_ar', how='left')

        gdf = gdf.drop(columns=['Code_Lat_y', 'Code_Long_y'], errors='ignore')
        gdf = gdf.rename(columns={'Code_Lat_x': 'Code_Lat', 'Code_Long_x': 'Code_Long'}, errors='ignore')
        
        return gdf, Paris_velo
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return None, None

def create_scatter_plot(gdf):
    fig = px.scatter(
        gdf, 
        x='year',  # Colonne pour l'axe X
        y='comptages_annuels',  # Colonne pour l'axe Y
        size='comptages_annuels',  # Pour la taille des points
        color='comptages_annuels',  # Pour la couleur des points
        hover_name='Localisation',  # Pour les noms au survol
        log_x=True,  # Echelle logarithmique pour l'axe X
        size_max=60  # Taille maximale des points
    )
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=300
    )
    return fig

def make_treemap(input_df, input_id, input_column, input_color_theme):
    if input_id in input_df.columns and input_column in input_df.columns:
        fig = px.treemap(
            input_df, 
            path=[input_id, input_column], 
            values=input_column,
            color=input_column, 
            color_continuous_scale=input_color_theme,  
            hover_data=[input_id, input_column]
        )
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=300
        )
        return fig
    else:
        st.error(f"Les colonnes '{input_id}' ou '{input_column}' sont manquantes dans les données.")
        return go.Figure()

def create_map(gdf):
    if 'Code_Lat' in gdf.columns and 'Code_Long' in gdf.columns:
        fig = px.scatter_mapbox(
            gdf,
            lat='Code_Lat',
            lon='Code_Long',
            color='comptages_annuels',
            size='comptages_annuels',
            color_continuous_scale=px.colors.cyclical.IceFire,
            size_max=40,
            zoom=9,
            center={"lat": 48.8566, "lon": 2.3522},
            mapbox_style="open-street-map",
            hover_name='l_ar',
            hover_data=['comptages_annuels', 'Localisation']
        )

        contour_Paris_geojson = 'Données/Contours.geojson'
        contour_gdf = gpd.read_file(contour_Paris_geojson)
        contour_Paris_geojson = contour_gdf.geometry.__geo_interface__

        for feature in contour_Paris_geojson['features']:
            coords = feature['geometry']['coordinates'][0]
            lon = [coord[0] for coord in coords]
            lat = [coord[1] for coord in coords]
            fig.add_trace(go.Scattermapbox(
                lon=lon,
                lat=lat,
                mode='lines',
                line=dict(width=2, color='black'),
                showlegend=False
            ))

        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=300
        )
        
        return fig

gdf, Paris_velo = load_data()

if gdf is not None and Paris_velo is not None:
    # Encadrement (sidebar)
    with st.sidebar:
        st.title('🚴 Comptage cyclable à Paris')
        
        year_list = list(Paris_velo.year.unique())[::-1]
        selected_year = st.selectbox('Select a year', year_list)
        df_selected_year = Paris_velo[Paris_velo.year == selected_year]
        df_selected_year_sorted = df_selected_year.sort_values(by="comptages_annuels", ascending=False)

        color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'viridis', 'rainbow', 'turbo', 'reds']
        selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

    # Créer les graphiques
    map_fig = create_map(gdf)
    treemap_fig = make_treemap(df_selected_year, 'l_ar', 'comptages_annuels', selected_color_theme)
    scatter_fig = create_scatter_plot(gdf)

    # Affichage dans Streamlit
    # Lignes pour Carte et Tableau des données
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('#### Répartition des vélos par arrondissement')
        st.plotly_chart(map_fig, use_container_width=True)

    with col2:
        st.markdown('#### Données par localisation')
        st.dataframe(df_selected_year_sorted,
                     column_order=("l_ar", "comptages_annuels"),
                     hide_index=True,
                     width=None,
                     column_config={
                        "l_ar": st.column_config.TextColumn("Arrondissement"),
                        "comptages_annuels": st.column_config.ProgressColumn(
                            "Comptages Annuels",
                            format="%f",
                            min_value=0,
                            max_value=max(df_selected_year_sorted.comptages_annuels),
                        )}
                     )

    # Treemap et Scatter Plot côte à côte
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('#### Comptages annuels par arrondissement')
        st.plotly_chart(treemap_fig, use_container_width=True)

    with col2:
        st.markdown('#### Distribution des comptages cyclables')
        st.plotly_chart(scatter_fig, use_container_width=True)

    # À propos de ce tableau de bord en dessous
    st.markdown('#### À propos de ce tableau de bord')
    st.write('''
        - **Source de données**: [Paris Open Data](https://opendata.paris.fr/explore/dataset/comptage-velo-donnees-compteurs/information/?disjunctive.id_compteur&disjunctive.nom_compteur&disjunctive.id&disjunctive.name).
        - :orange[**Répartition des vélos par arrondissement**]: Carte montrant les points de comptage cyclables à Paris pour l'année sélectionnée.
        - :orange[**Comptages annuels par arrondissement**]: Vue hiérarchique des comptages annuels par arrondissement.
        - :orange[**Données par localisation**]: Tableau des comptages annuels triés par arrondissement pour l'année sélectionnée.
        - :orange[**Distribution des comptages cyclables**]: Scatter plot montrant la distribution des comptages cyclables.
    ''')
