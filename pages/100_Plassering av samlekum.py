import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
from scipy.spatial import ConvexHull
import math
import random

from helpscripts._map import Map

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

def plot_eb(x, y, id = 1):
    plt.scatter(x, y, color = "blue", marker = ".")
    plt.annotate(id, (x, y))
    circle1 = plt.Circle((x, y), 15, linestyle = "--", fill = None, alpha = 0.1)
    plt.gca().add_patch(circle1)

def plot_sk(x, y, id = 1):
    plt.scatter(x, y, color = "red", marker = ".")
    plt.annotate(id, (x, y))

def plot_tr(x, y, id = 1):
    plt.scatter(x, y, color = "green", marker = ".")
    plt.annotate(id, (x, y))

def plot_point(x, y, id = 1):
    id_type = id[0:2].upper()
    if id_type == "EB":
        plot_eb(x, y, id)
    elif id_type == "SK":
        plot_sk(x, y, id)
    elif id_type == "TR":
        plot_tr(x, y, id)

def plot_line(point1 = [1, 2], point2 = [3, 4], line_length = 5, line_color = "black", line_alpha = 0.2):
    x_values = [point1[0], point2[0]]
    y_values = [point1[1], point2[1]]
    plt.plot(x_values, y_values, linestyle="-", color = line_color, alpha = line_alpha)
    pos_y1 = center_point(x_values[0], x_values[1], y_values[0], y_values[1])
    #plt.plot(pos_y1[0], pos_y1[1], color = "green", marker = ".")
    plt.annotate(f'{line_length}', xy =(0, 0), xytext =(pos_y1[0], pos_y1[1]))
  
def calculate_line_length(point1 = [1, 2], point2 = [3, 4]):
    x2, y2 = point2[0], point2[1]
    x1, y1 = point1[0], point1[1]
    length = abs((((x2-x1)**2) + ((y2-y1)**2))**(1/2))
    return int(round(length, 0))

def center_point(x1, x2, y1, y2):
    x_mid = ((x2 + x1))/2
    y_mid = ((y2 + y1))/2
    return x_mid, y_mid

def set_cx_cy(points_SK, points_EB):
    cx = points_SK[0][0]
    cy = points_SK[0][1]
    total_line_length = 0
    max_line_length = 0
    for i in range(0, len(points_EB)):
        line_length = calculate_line_length(point1 = [cx, cy], point2 = points_EB[i])
        if line_length > max_line_length:
            max_line_length = line_length
        total_line_length += line_length
    return cx, cy, total_line_length, max_line_length

def find_cx_cy(points, mode = "Iterasjon"):
    hull = ConvexHull(points)
    for simplex in hull.simplices:
        ax.plot(points[simplex, 0], points[simplex, 1], color = "red", linestyle = "--", alpha = 0.2)
    if mode == "Tyngdepunkt":
        cx = np.mean(hull.points[hull.vertices,0])
        cy = np.mean(hull.points[hull.vertices,1])
        total_line_length = 0
        max_line_length = 0
        for i in range(0, len(points)):
            line_length = calculate_line_length(point1 = [cx, cy], point2 = points[i])
            if line_length > max_line_length:
                max_line_length = line_length
            total_line_length += line_length
    elif mode == "Iterasjon":
        x_points = hull.points[hull.vertices,0]
        y_points = hull.points[hull.vertices,1]
        p1 = [int(np.min(x_points)), int(np.min(y_points))]
        p2 = [int(np.max(x_points)), int(np.max(y_points))]
        MLL, TLL, CX, CY = [], [], [], []
        for x in range(p1[0], p2[0]):
            for y in range(p1[0], p2[1]):
                cx, cy = x, y
                #--
                #ax.plot(cx, cy, marker = "o", color = "red")
                total_line_length = 0
                max_line_length = 0
                for i in range(0, len(points)):
                    line_length = calculate_line_length(point1 = [cx, cy], point2 = points[i])
                    if line_length > max_line_length:
                        max_line_length = line_length
                    total_line_length += line_length
                MLL.append(max_line_length)
                TLL.append(total_line_length)
                CX.append(cx)
                CY.append(cy)
        index = np.argmin(MLL)
        cx = CX[index]
        cy = CY[index]
        total_line_length = TLL[index]
        max_line_length = MLL[index]
    return cx, cy, total_line_length, max_line_length

def filter_dataframe(id):
    return df[df["ID"].str.contains(id)]

def add_random_eb(dataframe):
    df_copy = dataframe.copy()  # Create a copy of the dataframe to avoid modifying the original
    random_eb = f"EB{random.randint(1, 100)}"  # Generate a random EB value
    df_copy.loc[df_copy.shape[0]] = [random_eb, random.randint(-100, 100), random.randint(-100, 100)]  # Add the random EB row to the dataframe
    return df_copy
#--
st.title("Optimal plassering")

df = pd.DataFrame({
    "ID" : ["EB1", "EB2", "EB3", "EB4", "EB5", "EB6", "EB7", "TR", "SK1", "EB8"],
    "X" : [5, 35, 20, -10, -25, 20, -10, 50, 0, 60],
    "Y" : [5, 5, 31, 31, 5, -21, -21, 20, 50, 60]})

df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")

if st.checkbox('Kjør beregning'):

    fig, ax = plt.subplots()
    for i in range(0, len(df)):
        X, Y, ID = df["X"][i], df["Y"][i], df["ID"][i]
        plot_point(X, Y, ID)

    df_EB, df_TR, df_SK = filter_dataframe("EB"), filter_dataframe("TR"), filter_dataframe("SK")
    points_EB, points_TR, points_SK = df_EB[["X", "Y"]].to_numpy(dtype=float), df_TR[["X", "Y"]].to_numpy(dtype=float), df_SK[["X", "Y"]].to_numpy(dtype=float)

    selected_mode = st.selectbox("Modus", options=["Tyngdepunkt", "Iterasjon", "Egendefinert"])

    if selected_mode == "Egendefinert":
        cx, cy, total_line_length, max_line_length = set_cx_cy(points_SK, points_EB)
    else:
        cx, cy, total_line_length, max_line_length = find_cx_cy(points_EB, mode = selected_mode)

    ax.plot(cx, cy, marker = "o", color = "red")
    for i in range(0, len(points_EB)):
        line_length = calculate_line_length(point1 = [cx, cy], point2 = points_EB[i])
        plot_line(point1 = [cx, cy], point2 = points_EB[i], line_length = line_length)
    if len(points_TR) > 0:
        line_length = calculate_line_length(point1 = [cx, cy], point2 = [points_TR[0][0], points_TR[0][1]])  
        sk_to_tr_length = line_length  
        plot_line(point1 = [cx, cy], point2 = [points_TR[0][0], points_TR[0][1]], line_length = line_length, line_alpha = 0.5)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Maks (SK <-> EB)", f"{max_line_length} m")
    with c2:
        st.metric("Totalt (SK <-> EB)", f"{total_line_length} m")
    with c3:
        st.metric("SK <-> TR", f"{sk_to_tr_length} m")


    plt.xlabel('X [m]')
    plt.ylabel('Y [m]')
    plt.grid(True)
    plt.gca().set_aspect("equal")
    st.pyplot(plt)
    plt.close()
else:
    st.stop()