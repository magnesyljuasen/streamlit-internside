from scripts._utils import load_lottie

from streamlit_lottie import st_lottie

def load_page():
    lott = load_lottie("https://assets3.lottiefiles.com/packages/lf20_szeieqx5.json")
    st_lottie(lott)
    
