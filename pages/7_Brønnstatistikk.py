import streamlit as st

st.set_page_config(
    page_title="Grunnvarme",
    page_icon="🏔️",
)
with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

def show_gif(url, text, expanded = False):
    with st.expander(text, expanded=expanded):
        st.image(url, use_column_width=True)

st.title("Brønner i GRANADA")
gif_url_0 = "https://media.giphy.com/media/3tQX6TwhSkKhRN3dk2/giphy.gif"
gif_url_1 = "https://media.giphy.com/media/WrGaIXB7q7sCrwwIaH/giphy.gif"
gif_url_2 = "https://media.giphy.com/media/1QbSRec469DdCuBF5N/giphy.gif"
gif_url_3 = "https://media.giphy.com/media/U798z21RrYElOKzeD5/giphy.gif"
gif_url_4 = "https://media.giphy.com/media/sSIkFPPZfqjbLdUNmH/giphy.gif"
gif_url_5 = "https://media.giphy.com/media/Fl331J9xxw1xQDx1tc/giphy.gif"
gif_url_6 = "https://media.giphy.com/media/CjktpeW8ivBuwFzuCt/giphy.gif"
gif_url_7 = "https://media.giphy.com/media/MUGhxkFZVREP9kNlcD/giphy.gif"
gif_url_8 = "https://media.giphy.com/media/n0EAtml44LzuGRlE4G/giphy.gif"
gif_url_9 = "https://media.giphy.com/media/ip92yHhTbInGJTQjyx/giphy.gif"
gif_url_10 = "https://media.giphy.com/media/G12KvH51NckDw4w2OF/giphy.gif"
gif_url_00 = "https://media.giphy.com/media/RBHy8UO6i6agv33EHj/giphy.gif"

show_gif(gif_url_00, text="Totalt", expanded=True)
show_gif(gif_url_0, text="Sammenstilt", expanded=True)
show_gif(gif_url_10, text="Båsum")
show_gif(gif_url_6, text="Seabrokers")
show_gif(gif_url_5, text="Vestnorsk")
show_gif(gif_url_8, text="Kraft")
show_gif(gif_url_9, text="Rototec")
show_gif(gif_url_7, text="Aarsleff")
show_gif(gif_url_4, text="Universal")
show_gif(gif_url_1, text="Brødrene Myhre")
show_gif(gif_url_2, text="Værås")
show_gif(gif_url_3, text="Follo")















