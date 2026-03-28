import streamlit as st
import pandas as pd
import random
import time
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, ClientOptions

# ==============================================================================
# 0. SUPABASE KONEKCIJA (PROTIV RESETIRANJA U PONOĆ)
# ==============================================================================
# Podaci se povlače iz Streamlit Secrets (Settings > Secrets)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

# POPRAVAK ZA TYPEERROR: Eksplicitno definiramo opcije za stabilnu konekciju
options = ClientOptions(postgrest_client_timeout=10, gotrue_client_timeout=10)
supabase = create_client(url, key, options=options)

def ucitaj_iz_baze():
    try:
        res = supabase.table("turnir_podaci").select("podaci").eq("id", 1).execute()
        return res.data[0]["podaci"]
    except:
        return {"igraci": [], "krug": 0, "aparati": {}, "nagrade": "", "broj_pobjednika": 3}

def spremi_u_bazu(podaci):
    supabase.table("turnir_podaci").update({"podaci": podaci}).eq("id", 1).execute()

# ==============================================================================
# 1. KONFIGURACIJA I WAYNE ICON SETUP
# ==============================================================================
st.set_page_config(page_title="KRATZER MASTER", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=15000, key="wayne_3000_supabase_ver")

icon_url = "https://raw.githubusercontent.com/Mr180Wayne/kratzer/main/WAYNE_LOGO.jpg"

st.markdown(f"""
    <div style="display:none;">
        <head>
            <title>KRATZER MASTER</title>
            <link rel="icon" type="image/jpeg" href="{icon_url}">
            <link rel="apple-touch-icon" href="{icon_url}">
            <meta name="mobile-web-app-capable" content="yes">
            <meta name="theme-color" content="#0E1117">
        </head>
    </div>
""", unsafe_allow_html=True)

# Inicijalizacija - prvo gledamo u bazu, ne u lokalnu memoriju
if "db" not in st.session_state:
    st.session_state.db = ucitaj_iz_baze()

db = st.session_state.db
is_authenticated = "pass" in st.query_params and st.query_params["pass"] == "qweasd"

# ==============================================================================
# 2. LOGIKA - WAYNE KOD 3000 (IDENTIČNA, SAMO DODANO SPREMANJE)
# ==============================================================================
def dodaj_igraca_logika():
    ime = st.session_state.n_ime_in.strip().upper()
    if ime:
        db["igraci"].append({
            "Ime": ime, "Mrlje": 0, "Max": st.session_state.n_max_in,
            "Kotizacija": st.session_state.n_kot_in, "Status": "AKTIVAN", "Ispao_Kada": 0
        })
        spremi_u_bazu(db) # Odmah šalje u Supabase
        st.session_state.n_ime_in = ""

def generiraj_meceve(broj_aparata):
    aktivni = [i['Ime'] for i in db["igraci"] if i['Status'] == "AKTIVAN"]
    random.shuffle(aktivni)
    db["krug"] += 1
    db["aparati"] = {}
    for i in range(len(aktivni)):
        ap_id = (i % broj_aparata) + 1
        if ap_id not in db["aparati"]: db["aparati"][ap_id] = []
        db["aparati"][ap_id].append(aktivni[i])
    spremi_u_bazu(db) # Sprema krug i mečeve

# ==============================================================================
# 3. STIL - WAYNE MASTER DESIGN (55px) - NETAKNUTO
# ==============================================================================
u_igri_trenutno = len([i for i in db["igraci"] if i['Status'] == "AKTIVAN"])
ukupni_fond = sum([i['Kotizacija'] for i in db["igraci"]])

st.markdown(f"""
    <style>
    @media (min-width: 768px) {{
        [data-testid="stSidebar"] {{ min-width: 500px !important; max-width: 500px !important; }}
    }}
    .stApp {{ background-color: #0E1117; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 55px !important; }}
    
    .fixed-header {{
        position: fixed; top: 55px; left: 0; width: 100%; height: 75px;
        background-color: #1A1C24 !important; color: #00FFFF !important;
        display: flex; justify-content: center; align-items: center;
        z-index: 99; border-bottom: 3px solid #00FFFF;
        font-size: 24px; font-weight: bold;
    }}
    .main-content {{ margin-top: 135px; }}
    
    .reward-container {{ display: flex; flex-direction: column; align-items: center; gap: 15px; padding-bottom: 50px; }}
    .reward-card {{
        background: linear-gradient(145deg, #1e2029, #16181d); border: 2px solid #00FFFF;
        border-radius: 20px; padding: 25px; width: 90%; max-width: 450px; text-align: center;
    }}
    .trophy {{ font-size: 50px; }}
    .amount-text {{ color: #00FFA3; font-size: 42px; font-weight: bold; }}
    
    .table-container {{ width: 100%; max-width: 600px; margin: 0 auto; }}
    table.final-table {{ width: 100% !important; border-collapse: collapse !important; background: black; }}
    .c-idx {{ width: 50px !important; color: #888 !important; text-align: center !important; }}
    .c-name {{ width: 400px !important; text-align: left !important; padding-left: 20px !important; font-size: 28px !important; }}
    .c-mrlje {{ width: 100px !important; text-align: center !important; font-size: 36px !important; }}
    
    .aparat-box {{ background-color: #1A1C24; border: 4px solid #00FFFF; padding: 25px; border-radius: 15px; margin: 15px; text-align: center; color: #00FFA3 !important; font-size: 30px; }}
    </style>
    <div class="fixed-header">KRUG {db['krug']} | {u_igri_trenutno} IGRAČA | {ukupni_fond}€</div>
    <div class="main-content"></div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 4. SIDEBAR - ADMIN PANEL (IDENTIČNO, DODANO SPREMANJE)
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ ADMIN PANEL")
    sifra = st.text_input("", type="password", placeholder="Lozinka...")
    if sifra == "qweasd" or is_authenticated:
        if not is_authenticated: st.query_params["pass"] = "qweasd"
        
        with st.expander("👤 NOVI IGRAČ"):
            st.number_input("Max mrlja", 1, 10, 4, key="n_max_in")
            st.number_input("Kotizacija", 0, 1000, 10, key="n_kot_in")
            st.text_input("Ime", key="n_ime_in", on_change=dodaj_igraca_logika)
        
        db["broj_pobjednika"] = st.radio("Pobjednika:", [2, 3, 4, 5], index=[2,3,4,5].index(db["broj_pobjednika"]), horizontal=True)
        br_ap_in = st.number_input("Broj grupa", 1, 20, max(1, u_igri_trenutno // 4))
        if st.button("🎯 GENERIRAJ MEČEVE"): 
            generiraj_meceve(br_ap_in)
            st.rerun()

        st.divider()
        with st.expander("📉 KONTROLA IGRAČA", expanded=True):
            for idx, igrac in enumerate(db["igraci"]):
                col_i, col_p, col_m, col_d = st.columns([3, 1, 1, 1])
                boja_mrlja = "#00FFFF" if igrac['Status'] == "AKTIVAN" else "#FF4B4B"
                col_i.markdown(f"{igrac['Ime']} <br><b style='color:{boja_mrlja}'>({igrac['Mrlje']}/{igrac['Max']})</b>", unsafe_allow_html=True)
                
                if col_p.button("➕", key=f"p_{idx}"):
                    igrac['Mrlje'] += 1
                    if igrac['Mrlje'] >= igrac['Max']:
                        igrac['Status'] = "ELIMINIRAN"; igrac['Ispao_Kada'] = time.time()
                    spremi_u_bazu(db) # Sprema mrlju u bazu
                    st.rerun()
                
                if col_m.button("➖", key=f"m_{idx}"):
                    igrac['Mrlje'] = max(0, igrac['Mrlje'] - 1)
                    igrac['Status'] = "AKTIVAN"
                    spremi_u_bazu(db) # Sprema ispravak u bazu
                    st.rerun()
                
                if col_d.button("🗑️", key=f"del_{idx}"):
                    db["igraci"].pop(idx)
                    spremi_u_bazu(db)
                    st.rerun()

        if st.button("🔴 RESET SVE"): 
            db["igraci"], db["krug"], db["aparati"] = [], 0, {}
            spremi_u_bazu(db)
            st.rerun()

# ==============================================================================
# 5. GLAVNI PRIKAZ (TABS) - IDENTIČNO
# ==============================================================================
t_krug, t_tab, t_fond = st.tabs(["🎯 MEČEVI", "📊 TABLICA", "🏆 NAGRADE"])

with t_krug:
    if db["krug"] > 0:
        for br, par in db["aparati"].items():
            igraci_list_html = "".join([f"<div>{i}</div>" for i in par])
            st.markdown(f"<div class='aparat-box'><small style='color:#00FFFF;'>GRUPA {br}</small><br>{igraci_list_html}</div>", unsafe_allow_html=True)

with t_tab:
    if db["igraci"]:
        df = pd.DataFrame(db["igraci"]).sort_values(by=['Status', 'Ispao_Kada'], ascending=[True, False])
        html = '<div class="table-container"><table class="final-table">'
        for i, (_, r) in enumerate(df.iterrows(), 1):
            clr = "#00FFA3" if r['Status'] == "AKTIVAN" else "#FF4B4B"
            html += f'<tr style="color: {clr};"><td class="c-idx">{i}</td><td class="c-name">{r["Ime"]}</td><td class="c-mrlje">{r["Mrlje"]}</td></tr>'
        html += '</table></div>'; st.markdown(html, unsafe_allow_html=True)

with t_fond:
    st.markdown(f"<h1 style='text-align: center; color: #00FFFF;'>FOND: {ukupni_fond}€</h1>", unsafe_allow_html=True)
    br_pob = db["broj_pobjednika"]
    postotci = {2:[0.7,0.3], 3:[0.5,0.3,0.2], 4:[0.4,0.3,0.2,0.1], 5:[0.35,0.25,0.2,0.12,0.08]}[br_pob]
    trofeji = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    
    isplate = []
    temp_suma = 0
    for i in range(br_pob - 1):
        iznos = round((ukupni_fond * postotci[i]) / 5) * 5
        isplate.append(iznos)
        temp_suma += iznos
    isplate.append(ukupni_fond - temp_suma)
    
    st.markdown('<div class="reward-container">', unsafe_allow_html=True)
    for i in range(br_pob):
        st.markdown(f"""<div class='reward-card'><div class='trophy'>{trofeji[i]}</div><div>{i+1}. MJESTO</div><div class='amount-text'>{isplate[i]}€</div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
