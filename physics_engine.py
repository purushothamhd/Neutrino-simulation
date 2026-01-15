# physics_engine.py - NEUTRINO OSCILLATION RESEARCH
import time
import numpy as np
import queue
import math
from vector import Vector2D

# --- Constants for Neutrino Physics ---
# Mass Squared Differences (eV^2) - Based on current experimental data
# Solar Scale
DELTA_M2_21 = 7.53e-5
# Atmospheric Scale
DELTA_M2_31 = 2.51e-3 

# Speed of simulation (arbitrary units to make visualizer readable)
C_LIGHT_SIM = 200.0 

class Neutrino:
    def __init__(self, p_id, position, energy_mev, flavor_init):
        self.id = p_id
        self.position = position
        # Direction is fixed upon creation (neutrinos travel in straight lines)
        angle = np.random.uniform(-0.1, 0.1) # Narrow beam
        self.velocity = Vector2D(math.cos(angle), math.sin(angle)) * C_LIGHT_SIM
        
        self.energy = energy_mev # Energy in MeV
        self.distance_traveled = 0.0
        
        # State Vector [nu_e, nu_mu, nu_tau] (Complex amplitudes)
        # Initialize as pure flavor state
        if flavor_init == 'electron':
            self.state = np.array([1+0j, 0+0j, 0+0j], dtype=np.complex128)
        elif flavor_init == 'muon':
            self.state = np.array([0+0j, 1+0j, 0+0j], dtype=np.complex128)
        
        self.probs = np.abs(self.state)**2

    def propagate(self, dt, mixing_matrix, density_potential=0):
        """
        Evolve the quantum state using the Hamiltonian.
        L = Distance traveled = c * t
        """
        step_dist = self.velocity.magnitude() * dt
        self.distance_traveled += step_dist
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt

        # OSCILLATION CALCULATION
        # In a full simulation, we solve the Schrödinger equation: i d/dt |v> = H |v>
        # For visualization speed, we use the analytical transition probability approximation
        # P(a->b) = sin^2(2theta) * sin^2(1.27 * dm^2 * L / E)
        
        # We simulate the phase rotation of the mass eigenstates here
        # This is a simplified 3-flavor rotation for visualization purposes
        
        # Argument for the sine wave: (1.27 * delta_m^2 * L) / E
        # We scale L significantly to make oscillations visible on screen (800px)
        # Real L is km, Sim L is pixels. 
        scale_factor = 10000.0 
        
        arg_sol = (1.27 * DELTA_M2_21 * self.distance_traveled * scale_factor) / self.energy
        arg_atm = (1.27 * DELTA_M2_31 * self.distance_traveled * scale_factor) / self.energy
        
        # Update probabilities based on Distance and Energy
        # This is a visual approximation of 3-flavor mixing
        # Red = Electron, Green = Muon, Blue = Tau
        
        # Simple 2-flavor vacuum oscillation logic for clean visual demo:
        prob_survival = 1.0 - (math.sin(2 * 0.5) ** 2) * (math.sin(arg_atm) ** 2)
        
        # In this simplified visual model, we oscillate between Electron (Red) and Muon (Green)
        # High Energy = Longer wavelength
        # Low Energy = Shorter wavelength
        
        self.probs[0] = math.cos(arg_atm)**2  # Electron-ish
        self.probs[1] = math.sin(arg_atm)**2  # Muon-ish
        self.probs[2] = 0.0 # Tau (keeping it simple for 2D vis)

        # Apply Matter Effect (MSW) - Crude approximation
        # If density > 0, suppress mixing amplitude
        if density_potential > 0.5:
             self.probs[0] = 1.0 # Matter traps it in electron flavor (simplified)
             self.probs[1] = 0.0

def simulation_process(data_q, param_q):
    
    # Defaults
    energy_beam = 500.0 # MeV
    mixing_angle = 0.5  # Radians
    
    neutrinos = []
    particle_id_counter = 0
    tick = 0
    
    # Define a Matter Density Field (The "Lead Wall")
    matter_start_x = 400
    matter_width = 100
    
    running = False
    
    print("[Neutrino Physics] Quantum Simulation Init")
    
    while True:
        try:
            # Message Handling
            while True:
                try:
                    msg = param_q.get_nowait()
                    if 'command' in msg:
                        if msg['command'] == 'START': running = True
                        if msg['command'] == 'STOP': running = False
                    if 'params' in msg:
                        p = msg['params']
                        if 'beam_energy' in p: energy_beam = float(p['beam_energy'])
                except queue.Empty:
                    break

            if not running:
                time.sleep(0.1)
                continue

            # 1. EMITTER: Fire new neutrinos continuously
            if len(neutrinos) < 150 and tick % 5 == 0:
                # Start at left edge
                start_pos = Vector2D(10, np.random.uniform(250, 350))
                # Slight energy spread (Natural linewidth)
                e_spread = np.random.normal(energy_beam, energy_beam * 0.05)
                neutrinos.append(Neutrino(particle_id_counter, start_pos, e_spread, 'electron'))
                particle_id_counter += 1

            # 2. PHYSICS UPDATE
            dt = 0.016 # ~60 FPS
            
            surviving_neutrinos = []
            
            for nu in neutrinos:
                # Check Matter Density at current location
                density = 0.0
                if matter_start_x < nu.position.x < matter_start_x + matter_width:
                    density = 1.0 # High electron density region
                
                # Evolve State
                nu.propagate(dt, None, density_potential=density)
                
                # Remove if out of bounds
                if nu.position.x < 850:
                    surviving_neutrinos.append(nu)
            
            neutrinos = surviving_neutrinos

            # 3. DATA PACKING
            # We map Flavor Probabilities to RGB
            # R = Electron, G = Muon, B = Tau
            
            colors = []
            x_pos = []
            y_pos = []
            sizes = []
            
            for nu in neutrinos:
                x_pos.append(nu.position.x)
                y_pos.append(nu.position.y)
                
                # Color mixing based on quantum probability
                r = int(nu.probs[0] * 255)
                g = int(nu.probs[1] * 255)
                b = int(nu.probs[2] * 255)
                
                # Hex color string
                colors.append(f"#{r:02x}{g:02x}{b:02x}")
                sizes.append(6)

            packet = {
                'tick': tick,
                'agents': {
                    'x': x_pos,
                    'y': y_pos,
                    'color': colors, # Now purely flavor based
                    'size': sizes,
                    'outline_color': ['#FFFFFF'] * len(neutrinos) # No collision outline needed
                },
                'metrics': {
                    'avg_energy': energy_beam,
                    'count': len(neutrinos)
                }
            }
            
            data_q.put(packet)
            tick += 1
            time.sleep(dt)

        except Exception as e:
            print(f"Error: {e}")
            break
