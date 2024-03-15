import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, HeatMapWithTime
from streamlit_folium import st_folium
import random
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import cascaded_union, polygonize
from scipy.spatial import Delaunay
import numpy as np
from shapely.geometry import MultiLineString
import pygeos
import fiona
import geopandas

def concave_hull(points_gdf, alpha=35):
    if len(points_gdf) < 4:
        # When you have a triangle, there is no sense
        # in computing an alpha shape.
        return points_gdf.unary_union.convex_hull

    coords = pygeos.coordinates.get_coordinates(points_gdf.geometry.values.data)
    tri = Delaunay(coords)
    triangles = coords[tri.vertices]
    a = ((triangles[:,0,0] - triangles[:,1,0]) ** 2 + (triangles[:,0,1] - triangles[:,1,1]) ** 2) ** 0.5
    b = ((triangles[:,1,0] - triangles[:,2,0]) ** 2 + (triangles[:,1,1] - triangles[:,2,1]) ** 2) ** 0.5
    c = ((triangles[:,2,0] - triangles[:,0,0]) ** 2 + (triangles[:,2,1] - triangles[:,0,1]) ** 2) ** 0.5
    s = ( a + b + c ) / 2.0
    areas = (s*(s-a)*(s-b)*(s-c)) ** 0.5
    circums = a * b * c / (4.0 * areas)
    filtered = triangles[circums < (1.0 / alpha)]
    edge1 = filtered[:,(0,1)]
    edge2 = filtered[:,(1,2)]
    edge3 = filtered[:,(2,0)]
    edge_points = np.unique(np.concatenate((edge1,edge2,edge3)), axis = 0).tolist()
    m = MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return gpd.GeoDataFrame({"geometry": [cascaded_union(triangles)]}, index=[0], crs=points_gdf.crs)

@st.cache()
def upload_data(number_of_points):
    df1 = pd.read_excel("src/data/input/el_nett_trondheim.xlsx", sheet_name=0)
    df2 = pd.read_excel("src/data/input/el_nett_trondheim.xlsx", sheet_name=1)
    df1 = df1.head(number_of_points)
    trafo_list = df1["trafo"].unique()
    return df1, df2, trafo_list

@st.cache()
def color_generator(trafo_list):
    color_list = []
    for i in range(0, len(trafo_list)):
        color = "#%06x" % random.randint(0, 0xFFFFFF)
        color_list.append(color)
    return color_list

def power_grid():
    st.title("Data fra Tensio")
    with st.form("s"):
        st.caption("Det er 115 118 adressepunkter i datasettet. Det tar lang tid å vise alle på kart (særlig for *adresser*)")
        number_of_points = st.number_input("Antall punkter", value = 100, max_value=115118, step = 100)
        st.form_submit_button("Start!")
        #--
    st.markdown("*Velg type kartvisning*")
    c1, c2 = st.columns(2)
    with c1:
        address_display = st.checkbox("Adresser", value=True)
    with c2:
        address_trafo_display = st.checkbox("Adresser tilknyttet samme trafo", value=True)
    df1, df2, trafo_list = upload_data(number_of_points)
    color_list = color_generator(trafo_list)
    with st.expander("Data"):
        st.write(df1)
        st.write(df2)
    #--
    m = folium.Map(location=[63.446827, 10.421906], zoom_start=11)
    #alpha = st.number_input("Alpha (Delaunay-triangulering)", value=600)
    for i in range(0, len(trafo_list)):
        df_plot = df1.loc[df1['trafo'] == trafo_list[i]]
        lat_point_list= df_plot["lat"]
        lng_point_list = df_plot["lng"]
        if len(lat_point_list) > 4:
            #df = pd.DataFrame({"Latitude" : lat_point_list, "Longitude" : lng_point_list})
            #gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.Longitude, df.Latitude))
            #concave_gdf = concave_hull(gdf, alpha)
            #concave_gdf.set_crs(epsg = "4326", inplace = True)
            #concave_gdf = concave_gdf.to_json()
        
            trafo_name = df_plot["trafo"].iloc[0]
            df2_row = df2.loc[df2["trafo"] == trafo_name]
            polygon_geom = Polygon(zip(lng_point_list, lat_point_list))
            polygon_geom2 = polygon_geom.convex_hull
            #--
            #text = "hei"
            text = f""" 
            Trafo: <strong>{trafo_name}</strong></br> \
            Antall energimålere (AV | TRD): <strong>{len(lat_point_list)} | {df2_row["energimålere"].iloc[0]}</strong></br> \
            Kapasitet (TRD): <strong>{round(df2_row["performance (kW)"].iloc[0] * 10/1000, 2)} GW</strong></br> \   
            """
            #--
            if address_trafo_display:
                #points = folium.features.GeoJson(concave_gdf)
                #m.add_child(points)
                folium.GeoJson(polygon_geom2, style_function=lambda x: {'fillColor': 'orange'}, tooltip=text).add_to(m)
            if address_display:
                df_plot.apply(lambda row:folium.CircleMarker(location=[row["lat"], row["lng"]], radius=5, tooltip=row["trafo"], color=color_list[i]).add_to(m), axis=1)
    st_folium(m, width=725, returned_objects=[])
    st.markdown("---")
    st.caption("- Knytte trafo til kapasitet")
    st.caption("- Knytte trafo til nettstasjon")
    st.caption("- Heat map(?)")


    #--
    #df2 = pd.read_excel("src/data/input/el_nett_trondheim.xlsx", sheet_name=1)
    #st.write(df2)
    #st.write(df1["trafo"].unique())









