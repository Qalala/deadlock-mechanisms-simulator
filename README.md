# Deadlock Mechanisms Simulator

A desktop GUI simulator that visualizes classic operating-systems deadlock mechanisms on a **resource-allocation graph**. You can build processes and resources interactively, draw request/assignment edges, and switch between **Detection**, **Avoidance** (Banker's algorithm), and **Prevention** (resource ordering) modes.

The stack is:
- **Language / UI**: Python 3 + Tkinter
- **Graph model**: NetworkX directed graphs for processes, resources, and edges

This project is meant for coursework demos and self-study: instead of only reading matrices on a whiteboard, you see the graph update live and get blocked/allowed feedback as you assign resources.

## Tech stack
- Python 3
- Tkinter (GUI)
- NetworkX (resource-allocation graphs / cycle detection helpers)

## Architecture (high level)

```
resource_allocation_sim.py
├─ ResourceAllocationGraph
│  ├─ add_resource / add_process
│  ├─ add_request_edge / add_assignment_edge
│  ├─ detect_deadlock()          [Detection mode]
│  ├─ bankers_algorithm()        [Avoidance mode]
│  ├─ resource_ordering_valid()  [Prevention mode]
│  └─ matrices: Max / Allocation / Need / Available
└─ App (Tkinter)
   ├─ mode selector: Detection | Avoidance | Prevention
   ├─ canvas drawing (nodes + colored edges)
   ├─ Check / Show Data Structures / Reset
   └─ dialogs for names, instances, allocations

Guide.txt
└─ step-by-step operator guide used during demos
```

### Visual legend
- **Blue circle** = process
- **Orange rectangle** = resource (with instance counts)
- **Red arrow** = process requests / claims a resource
- **Green arrow** = resource instances assigned to a process

### Mode behavior

- **Detection**
  - Allows arbitrary claim/assign combinations.
  - **Check** runs deadlock analysis (cycle-oriented detection on the allocation graph).
  - Useful for deliberately constructing unsafe / deadlocked scenarios.

- **Avoidance (Banker's algorithm)**
  - On **Assign Edge**, the simulator asks Banker's algorithm whether the allocation keeps the system in a **safe** state.
  - Unsafe requests are **blocked** with a warning.
  - Matrices (`Max`, `Allocation`, `Need`, `Available`) stay consistent with claims and assignments.

- **Prevention (resource ordering)**
  - Enforces a simple ordering policy (alphabetical resource order in this implementation).
  - A process that already holds a “higher” resource cannot request a “lower” one.
  - Invalid claims are blocked immediately; no separate Check pass is required for the ordering rule.

### Data structures shown in the UI
- **Max matrix** — each process’s maximum need per resource
- **Allocation matrix** — currently held instances
- **Need matrix** — remaining need (`Max − Allocation`)
- **Available vector** — free instances per resource

---

## Running the project

### Prerequisites
- Python 3.8+
- `tkinter` (bundled with most Windows Python installs)
- `networkx`

### Install dependencies

```bash
pip install networkx
```

### Start the app

```bash
python resource_allocation_sim.py
```

A Tkinter window opens with the sidebar controls and drawing canvas.

---

## How to navigate the repo
- `resource_allocation_sim.py` — full application (graph logic + GUI)
- `Guide.txt` — detailed click-by-click usage notes
- `.gitignore` — ignores local caches / virtualenvs

---

## Demo walkthrough

1. Click **Add Resource**, name it `R1`, set instances (e.g. `3`).
2. Add another resource `R2` with instances `2`.
3. Click **Add Process** for `P1` and `P2`.
4. Select mode:
   - Start with **Detection** to freely build edges.
5. Use **Claim Request Edge** to set each process’s max need.
6. Use **Assign Edge** to allocate instances.
7. Click **Check** (Detection) or watch Banker's deny/allow messages (Avoidance).
8. Open **Show Data Structures** to inspect matrices.
9. Click **Reset** to clear the scenario.

### Tips
- Create resources/processes **before** edges.
- Use unique names and positive instance counts.
- In Avoidance mode, try an allocation that would exceed a safe state to see the block message.
- In Prevention mode, attempt an out-of-order claim to see the ordering guard.

---

## Project purpose
Teach and demonstrate deadlock **detection**, **avoidance**, and **prevention** with an interactive resource-allocation graph instead of static slides alone.
