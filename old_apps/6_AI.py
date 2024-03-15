import streamlit as st
import openai

st.set_page_config(page_title="AI", page_icon="🖥️")

with open("styles/main.css") as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True) 

# Define OpenAI API key 
openai.api_key = st.secrets["openai_apikey"]

st.title("Tekstgenerator")
st.markdown("""Appen benytter seg av modellen *text-davinci-003* fra *GPT-3 Open AI*.""")
with st.expander("Eksempler"):
    st.write(" • Hvilke forretningsmområder kan vi fokusere mer på når det gjelder bygging av grunnvarmeanlegg?")
    st.write(" • Skriv en tekst om hvorfor man bør velge grunnvarme til sin bolig. Teksten må ha et salgspreg.")
    st.write(" • Forklar grunnvarme til en 6 åring")
    st.write(" • Hva er fordelene med energibrønner?")
    st.write(" • Hva er de største barrierene når det gjelder grunnvarmeanlegg?")
    
st.header("Inndata")
# Set up the model and prompt
model_engine = "text-davinci-003"
prompt = st.text_input("Hva skal jeg skrive?")
temperature = st.slider("Kreativitet", min_value=0.0, value=0.5, max_value=1.0, step=0.1)
with st.spinner("Skriver..."):
    if prompt:
        st.header("Respons")
        # Generate a response
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=4000,
            n=3,
            stop=None,
            temperature=temperature,
        )

        for i in range(0, len(completion.choices)):
            st.markdown("---")
            st.write(completion.choices[i].text)
            