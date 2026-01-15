# visualizer.py - FIXED FOR NEUTRINO SIMULATION
import queue
import signal
import sys
import time
from collections import deque

# --- ESSENTIAL IMPORTS (This fixes your NameError) ---
from bokeh.plotting import figure 
from bokeh.models import ColumnDataSource, BoxAnnotation, Label
from bokeh.layouts import row, column
from bokeh.server.server import Server

def visualization_process(data_q):
    """Main visualization process that runs Bokeh server"""
    print("[Visualizer] Process started.")
    
    server = None
    
    def cleanup_and_exit(signum=None, frame=None):
        print("[Visualizer] Cleaning up...")
        if server:
            try:
                server.stop()
            except:
                pass
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)
    
    def bokeh_app(doc):
        # 1. Data Sources
        # We now accept 'color' directly as hex strings from the physics engine
        agent_source = ColumnDataSource(data={
            'x': [], 'y': [], 'color': [], 'size': []
        })
        
        # 2. Main Plot (The Neutrino Chamber)
        p1 = figure(
            height=600, width=800,
            title="Neutrino Oscillation Detector (Red=Electron, Green=Muon)",
            x_range=(0, 800), y_range=(0, 600),
            match_aspect=True,
            tools="pan,wheel_zoom,reset"
        )
        p1.background_fill_color = "#000000"
        p1.grid.grid_line_color = "#111111"

        # 3. The Matter Zone (Visualizing the MSW Effect Area)
        # This draws the yellow box where density is high
        matter_zone = BoxAnnotation(left=400, right=500, fill_color='yellow', fill_alpha=0.15)
        p1.add_layout(matter_zone)
        
        matter_label = Label(x=405, y=570, text="Dense Matter (Lead)", text_color="#FFFF00", text_font_size="10pt")
        p1.add_layout(matter_label)

        # 4. Render the Neutrinos
        # Note: color='color' tells Bokeh to look at the 'color' column in the data source
        p1.scatter(
            x='x', y='y',
            size='size',
            color='color', 
            line_color=None,
            fill_alpha=0.8,
            marker='circle',
            source=agent_source
        )

        # 5. Metrics Plot (Optional: Track Beam Count)
        # Simple placeholder to keep layout consistent
        p2 = figure(height=150, width=800, title="Beam Status", x_axis_label="Tick", y_axis_label="Active Particles")
        # (We can expand this later, keeping it empty prevents errors if data is missing)

        def update():
            try:
                # Drain queue to get latest frame
                data = None
                while True:
                    data = data_q.get_nowait()
            except queue.Empty:
                pass

            if data is not None:
                try:
                    agents = data['agents']
                    # Direct mapping of physics data to Bokeh source
                    agent_source.data = {
                        'x': agents['x'],
                        'y': agents['y'],
                        'color': agents['color'],
                        'size': agents['size']
                    }
                except KeyError as e:
                    print(f"Key Error in Viz: {e}")

        doc.add_periodic_callback(update, 33) # 30 FPS
        doc.add_root(column(p1, p2))
        doc.title = "Neutrino Research"

    # Server Setup
    try:
        server = Server(
            {'/': bokeh_app},
            num_procs=1,
            port=5006,
            allow_websocket_origin=["*"]
        )
        server.start()
        print("[Visualizer] Bokeh server running on port 5006")
        server.io_loop.start()
        
    except OSError:
        print("[Visualizer] Port 5006 busy. Kill old process.")
    except Exception as e:
        print(f"[Visualizer] Error: {e}")
    finally:
        cleanup_and_exit()
