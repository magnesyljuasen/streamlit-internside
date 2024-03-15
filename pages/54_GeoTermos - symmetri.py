import streamlit as st 
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.title("GeoTermos - Symmetri")

def rectangular_plot(distance = 5, area_x = 55, area_y = 55):
    # Generate x, y data
    x = np.arange(0, area_x, distance)  # Example x values
    y = np.arange(0, area_y, distance)  # Example y values

    # Create a meshgrid
    X, Y = np.meshgrid(x, y)

    # Flatten the meshgrid coordinates
    X_flat = X.flatten()
    Y_flat = Y.flatten()

    # Plotting
    plt.scatter(X_flat, Y_flat, c='blue')
    plt.xlabel('X [meter]')
    plt.ylabel('Y [meter]')
    plt.title(f'{len(X_flat)} brønner; Areal {max(x) * max(y)} m2')
    plt.grid(True)

    # Set aspect ratio to equal to make the grid cells square
    plt.gca().set_aspect('equal')

    # Show the plot
    st.pyplot(plt)
    plt.close()
    
def hexagon_plot(distance = 5, area_x = 55, area_y = 55):
    # Generate x, y data
    x = np.arange(0, area_x, distance)  # Example x values
    y = np.arange(0, area_y, distance)  # Example y values
    
    x_1 = x.copy()
    y_1 = y.copy()

    # Create a meshgrid
    X, Y = np.meshgrid(x, y)

    # Flatten the meshgrid coordinates
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    
    for i, (x, y) in enumerate(zip(X_flat, Y_flat)):
        hexagon_x = [x, x + distance, x + distance, x, x - distance, x - distance]
        hexagon_y = [y + distance, y + distance/2, y - distance/2, y - distance, y - distance/2, y + distance/2]
        plt.plot(hexagon_x + [hexagon_x[0]], hexagon_y + [hexagon_y[0]], color='black')


    # Plotting
    #plt.scatter(X_flat, Y_flat, c='blue')
    plt.xlabel('X [meter]')
    plt.ylabel('Y [meter]')
    plt.title(f'{len(X_flat)} brønner; Areal {max(x_1) * max(y_1)} m2')
    plt.grid(True)

    # Set aspect ratio to equal to make the grid cells square
    plt.gca().set_aspect('equal')

    # Show the plot
    st.pyplot(plt)
    plt.close()

distance = st.number_input("Avstand mellom brønner [m]", value = 5)
area_x = st.number_input("Lengde X [m]", value = 50, step = distance)
area_y = st.number_input("Lengde Y [m]", value = 50, step = distance)
hexagon_plot(distance=distance, area_x=area_x, area_y=area_y)


