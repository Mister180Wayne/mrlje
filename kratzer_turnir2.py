import streamlit as st
import pandas as pd
import random
import time

# --- 1. KONFIGURACIJA I VIZUAL ---
st.set_page_config(page_title="Kratzer Tournament Master", layout="wide")

# Session state za praćenje promjena (da znamo kad zazvoniti)
if 'last_change' not in st.session_state: st.session_state.last_change = 0
if 'igraci' not in st.session_state: st.session_state.igraci = []
if 'krug' not in st.session_state: st.session_state.krug = 1
if 'aparati' not in st.session_state: st.session_state.aparati = {}

with st.sidebar:
    st.title("⚙️ Kontrolna Ploča")
    font_size = st.slider("Veličina fonta", 16, 80, 32)
    st.divider()
    sifra = st.text_input("Admin Šifra", type="password")
    admin_mode = (sifra == "wayne123") # Ovdje stavi st.secrets["admin_password"] ako si postavio Secrets

# --- 2. AUDIO & FLASH LOGIKA (JavaScript) ---
# Dodajemo skriveni audio element i JS funkciju koja reagira na promjenu 'last_change'
st.markdown("""
    <audio id="ring_sound" src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" preload="auto"></audio>
    <script>
    function notifyPlayer() {
        var audio = document.getElementById("ring_sound");
        audio.play();
        // Bljesak ekrana
        document.body.style.backgroundColor = "#00FFA3";
        setTimeout(function(){ document.body.style.backgroundColor = "#0E1117"; }, 500);
    }
    </script>
    """, unsafe_allow_html=True)

# Custom CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #E0E0E0; transition: background-color 0.5s ease; }}
    table {{ background-color: black !important; width: 100% !important; border-collapse: collapse !important; }}
    th {{ background-color: #1A1C24 !important; color: #00FFA3 !important; font-size: {font_size}px !important; text-align: left !important; padding: 10px !important; }}
    td {{ background-color: black !important; font-size: {font_size}px !important; padding: 10px !important; font-weight: bold !important; }}
    .aparat-box {{ background-color: #1A1C24; border: 2px solid #00FFA3; padding: 20px; border-radius: 10px; margin-bottom: 15px; font-size: {font_size}px; color: white; }}
    </style>
    """, unsafe_allow_html=True)

# Funkcija koja okida obavijest
def trigger_alert():
    st.session_state.last_change = time.time()
    st.components.v1.html(f"""<script>window.parent.notifyPlayer();</script>""", height=0)

# --- 3. ADMIN FUNKCIJE ---
def dodaj_igraca():
    if st.session_state.novo_ime:
        st.session_state.igraci.append({
            "Ime": st.session_state.novo_ime, "Mrlje": 0, "Max": st.session_state.n_mmax, 
            "Kotizacija": st.session_state.n_kot, "Status": "AKTIVAN", "Ispao_Kada": 0
        })
        st.session_state.novo_ime = ""

if admin_mode:
    with st.sidebar:
        st.subheader("👤 Prijava Igrača")
        st.number_input("Max Mrlja", 1, 6, 4, key="n_mmax")
        st.number_input("Kotizacija (€)", 1, 100, 10, key="n_kot")
        st.text_input("Ime i prezime", key="novo_ime", on_change=dodaj_igraca)
        
        st.divider()
        st.subheader("🎲 Aparati")
        aktivni_lista = [i for i in st.session_state.igraci if i['Status'] == "AKTIVAN"]
        if aktivni_lista:
            prijedlog = max(1, len(aktivni_lista) // 4)
            odabrani_br = st.slider("Broj aparata:", 1, max(2, len(aktivni_lista)), prijedlog)
            if st.button("🚀 NOVI KRUG"):
                st.session_state.krug += 1
                random.shuffle(aktivni_lista)
                st.session_state.aparati = {i+1: [] for i in range(odabrani_br)}
                for idx, igrac in enumerate(aktivni_lista):
                    st.session_state.aparati[(idx % odabrani_br) + 1].append(igrac['Ime'])
                trigger_alert() # OBAVIJEST
                st.rerun()

# --- 4. GLAVNI EKRAN ---
st.title("🏆 KRATZER MASTER")

# ZVUČNI PREKIDAČ - Važno za mobilne uređaje!
with st.expander("🔔 Postavke obavijesti (KLIKNI ZA ZVUK)"):
    st.write("Preglednici blokiraju zvuk dok ga jednom ne pokrenete. Kliknite gumb ispod.")
    if st.button("Aktiviraj Zvuk"):
        st.components.v1.html("""<script>var audio = window.parent.document.getElementById("ring_sound"); audio.play();</script>""", height=0)

tab1, tab2 = st.tabs(["🎯 GRUPE", "📊 POREDAK"])

with tab1:
    st.header(f"Krug: {st.session_state.krug}")
    if st.session_state.aparati:
        cols = st.columns(min(len(st.session_state.aparati), 4))
        for i, (br, imena) in enumerate(st.session_state.aparati.items()):
            with cols[i % 4]:
                st.markdown(f'<div class="aparat-box"><b>APARAT {br}</b><br>{"<br>".join(imena)}</div>', unsafe_allow_html=True)

with tab2:
    if st.session_state.igraci:
        fond = sum(i['Kotizacija'] for i in st.session_state.igraci)
        st.write(f"Fond: **{fond} €**")
        df = pd.DataFrame(st.session_state.igraci).sort_values(by=['Status', 'Ispao_Kada'], ascending=[True, False])
        df.index = range(1, len(df) + 1)
        df.index.name = "Br."
        
        def style_text(row):
            colors = []
            for val in row:
                if row['Status'] == "ELIMINIRAN": colors.append('color: #555555')
                elif row['Mrlje'] == 0: colors.append('color: #00FFA3')
                elif row['Mrlje'] == row['Max'] - 1: colors.append('color: #FFD700')
                else: colors.append('color: white')
            return colors
        st.table(df[['Ime', 'Mrlje', 'Max', 'Status']].style.apply(style_text, axis=1))

# --- 5. ADMIN REZULTATI ---
if admin_mode and st.session_state.igraci:
    st.divider()
    colA, colB, colC = st.columns(3)
    with colA:
        izbor = st.selectbox("Poraz (+1 mrlja):", [i['Ime'] for i in st.session_state.igraci if i['Status'] == "AKTIVAN"])
        if st.button("Upiši Poraz"):
            for i in st.session_state.igraci:
                if i['Ime'] == izbor:
                    i['Mrlje'] += 1
                    if i['Mrlje'] >= i['Max']:
                        i['Status'] = "ELIMINIRAN"
                        i['Ispao_Kada'] = time.time()
            trigger_alert() # OBAVIJEST
            st.rerun()
    with colC:
        if st.button("🔴 RESTART"):
            st.session_state.igraci, st.session_state.aparati, st.session_state.krug = [], {}, 1
            st.rerun()