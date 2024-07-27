# 🚴 Tableau d'observation du comptage cyclable à Paris

Ce tableau de bord prend en charge des données open source et a été monté avec VSCode en Python.

## Bibliothèques utlisés dans l'appli
import pandas as pd
import geopandas as gpd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

## Source de données
Le comptage annuel des vélos à Paris est extraite de [Open Data Paris] via (https://opendata.paris.fr/explore/dataset/comptage-velo-donnees-compteurs/information/?disjunctive.id_compteur&disjunctive.nom_compteur&disjunctive.id&disjunctive.name).