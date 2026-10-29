# Deadlock Mechanisms Simulator

## Brief description
A desktop GUI simulator that visualizes deadlock **detection**, **prevention**, and Banker's **avoidance** using a resource-allocation graph.

## Project purpose
Demonstrate classic operating-systems deadlock mechanisms interactively: build processes/resources, claim and assign edges, then analyze safety or deadlocks with clear visual feedback.

## Project requirements
- Python 3.8+
- Packages: `tkinter` (usually bundled with Python on Windows), `networkx`

Install dependencies:

```bash
pip install networkx
```

## How to navigate
- `resource_allocation_sim.py` — main application (GUI + algorithms)
- `Guide.txt` — detailed usage guide for each mode

## How to run

```bash
python resource_allocation_sim.py
```

### Quick usage
1. Add resources and processes from the toolbar.
2. Choose a mode: **Detection**, **Avoidance** (Banker's), or **Prevention**.
3. Create claim/assign edges, then use **Check** / **Show Data Structures** as needed.
4. Use **Reset** to clear the graph.

### Visual legend
- Blue circle = process
- Orange rectangle = resource
- Red arrow = request
- Green arrow = assignment
