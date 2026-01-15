# simulation_app.py - NEUTRINO LAB INTERFACE
import streamlit as st
import multiprocessing as mp
import time
from physics_engine import simulation_process
from visualizer import visualization_process

st.set_page_config(layout="wide", page_title="Neutrino Oscillation Research")

# State Init
if 'sim_running' not in st.session_state:
    st.session_state.sim_running = False
    st.session_state.data_q = mp.Queue()
    st.session_state.param_q = mp.Queue()

st.title("Neutrino Oscillation & MSW Effect Simulator")

# Mathematical Context
st.latex(r'''
P(\nu_\alpha \rightarrow \nu_\beta) = \sin^2(2\theta) \sin^2\left(\frac{1.27 \Delta m^2 L}{E}\right)
''')
st.markdown("""
**Research Goal:** Observe how **Energy ($E$)** affects the **Oscillation Length ($L$)** and how matter density (the MSW effect) locks the flavor state.
* **Red:** Electron Flavor ($\nu_e$)
* **Green:** Muon Flavor ($\nu_\mu$)
* **Yellow Zone:** High density matter (Lead/Earth core)
""")

# Controls
col1, col2 = st.columns(2)
with col1:
    beam_energy = st.slider("Beam Energy (MeV)", 100.0, 5000.0, 500.0, step=100.0,
                           help="Higher energy = Longer wavelength (slower oscillation)")
    
with col2:
    if st.button("Start Beam"):
        if not st.session_state.sim_running:
            p_sim = mp.Process(target=simulation_process, args=(st.session_state.data_q, st.session_state.param_q))
            p_vis = mp.Process(target=visualization_process, args=(st.session_state.data_q,))
            p_sim.start()
            p_vis.start()
            st.session_state.sim_running = True
            st.session_state.param_q.put({'command': 'START'})

    if st.button("Stop Beam"):
        st.session_state.param_q.put({'command': 'STOP'})
        # (Cleanup logic here...)

# Live Update
if st.session_state.sim_running:
    st.session_state.param_q.put({'params': {'beam_energy': beam_energy}})

st.components.v1.iframe("http://localhost:5006", height=600)
