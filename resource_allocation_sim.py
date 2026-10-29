import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, Text, Scrollbar
import networkx as nx

NODE_RADIUS = 30

# -------- Resource Allocation Graph Logic --------
class ResourceAllocationGraph:
    def __init__(self):
        self.G = nx.DiGraph()
        self.node_pos = {}
        self.resources = {}  # name -> {'instances':int, 'allocated':int}
        self.processes = set()
        self.request_edges = set()
        self.assignment_edges = set()
        # Data structures for Banker's/Matrix Display
        self.max_matrix = {}
        self.allocation_matrix = {}
        self.need_matrix = {}
        self.available_vector = {}

    def clear(self):
        self.G.clear()
        self.node_pos.clear()
        self.resources.clear()
        self.processes.clear()
        self.request_edges.clear()
        self.assignment_edges.clear()
        self.max_matrix.clear()
        self.allocation_matrix.clear()
        self.need_matrix.clear()
        self.available_vector.clear()

    def add_resource(self, name, instances):
        self.resources[name] = {'instances': instances, 'allocated': 0}
        self.G.add_node(name, type='resource')

    def add_process(self, name):
        self.processes.add(name)
        self.G.add_node(name, type='process')
        # Initialize matrices
        if name not in self.max_matrix:
            self.max_matrix[name] = {}
            self.allocation_matrix[name] = {}
            self.need_matrix[name] = {}
        for r in self.resources:
            self.max_matrix[name][r] = 0
            self.allocation_matrix[name][r] = 0
            self.need_matrix[name][r] = 0

    def update_after_resource_add(self, r):
        for p in self.processes:
            self.max_matrix[p][r] = 0
            self.allocation_matrix[p][r] = 0
            self.need_matrix[p][r] = 0

    def add_request_edge(self, process, resource, max_need=None):
        # Add a request edge (P->R)
        self.G.add_edge(process, resource, type='request')
        self.request_edges.add((process, resource))
        # Update matrices (assume user sets max_need)
        if max_need is not None:
            self.max_matrix[process][resource] = max_need
            self.need_matrix[process][resource] = max_need - self.allocation_matrix[process][resource]

    def add_assignment_edge(self, resource, process, allocation=1):
        # Assignment edge (R->P): means R assigned to P
        self.G.add_edge(resource, process, type='assignment')
        self.assignment_edges.add((resource, process))
        self.allocation_matrix[process][resource] += allocation
        # Update need
        self.need_matrix[process][resource] = self.max_matrix[process][resource] - self.allocation_matrix[process][resource]
        # Reduce available vector
        if resource not in self.available_vector:
            self.available_vector[resource] = self.resources[resource]['instances']
        self.available_vector[resource] -= allocation

    def recalc_available(self):
        # Recalculate available vector
        self.available_vector = {r:self.resources[r]['instances'] for r in self.resources}
        for (resource, process) in self.assignment_edges:
            alloc = self.allocation_matrix[process][resource]
            self.available_vector[resource] -= alloc

    def detect_deadlock(self):
        # Use simple cycle detection
        try:
            cycles = list(nx.simple_cycles(self.G))
            if cycles:
                return True, cycles
            else:
                return False, []
        except Exception:
            return False, []

    def bankers_algorithm(self, req_proc, req_resource, req_amount):
        # Build a copy of matrices to simulate the request
        work = self.available_vector.copy()
        allocation = {p: self.allocation_matrix[p].copy() for p in self.allocation_matrix}
        need = {p: self.need_matrix[p].copy() for p in self.need_matrix}
        # Check request is <= need and <= available
        if req_amount > need[req_proc][req_resource]:
            return False, "Request exceeds process need."
        if req_amount > work[req_resource]:
            return False, "Request exceeds available resources."
        # Pretend to grant request
        work[req_resource] -= req_amount
        allocation[req_proc][req_resource] += req_amount
        need[req_proc][req_resource] -= req_amount
        # Safety algorithm
        finish = {p: False for p in self.processes}
        while True:
            found = False
            for p in self.processes:
                if not finish[p] and all(need[p][r] <= work[r] for r in self.resources):
                    for r in self.resources:
                        work[r] += allocation[p][r]
                    finish[p] = True
                    found = True
            if not found:
                break
        if all(finish.values()):
            return True, "Safe! Request can be granted."
        else:
            return False, "Unsafe! Request would lead to deadlock."

    def resource_ordering_valid(self, process, resource):
        # Simple prevention: Enforce process can only request resources in a certain order (alphabetical)
        order = sorted(self.resources.keys())
        req_index = order.index(resource)
        for r in self.resources:
            if self.allocation_matrix[process][r] > 0 and order.index(r) > req_index:
                return False
        return True

# -------- GUI --------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Resource Allocation Graph Simulator")
        self.graph = ResourceAllocationGraph()
        self.mode = tk.StringVar(value="Detection")
        self.selected_process = None
        self.selected_resource = None

        # --- UI Layout ---
        self.toolbar = tk.Frame(root)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Button(self.toolbar, text="Add Resource", command=self.add_resource).pack(fill=tk.X)
        tk.Button(self.toolbar, text="Add Process", command=self.add_process).pack(fill=tk.X)
        tk.Button(self.toolbar, text="Claim Request Edge", command=self.claim_request_edge).pack(fill=tk.X)
        tk.Button(self.toolbar, text="Assign Edge", command=self.assign_edge).pack(fill=tk.X)
        tk.Label(self.toolbar, text="Mode:").pack(pady=4)
        for mode in ["Detection", "Avoidance", "Prevention"]:
            tk.Radiobutton(self.toolbar, text=mode, variable=self.mode, value=mode).pack(anchor=tk.W)
        tk.Button(self.toolbar, text="Check", command=self.check_state).pack(fill=tk.X)
        tk.Button(self.toolbar, text="Show Data Structures", command=self.show_matrices).pack(fill=tk.X)
        tk.Button(self.toolbar, text="Reset", command=self.reset).pack(fill=tk.X)

        self.status = tk.Label(self.toolbar, text="Status: Ready", fg="blue")
        self.status.pack(fill=tk.X, pady=8)

        self.canvas = tk.Canvas(root, bg='white', width=820, height=520)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.graph.canvas = self.canvas
        self.layout_nodes()

    def add_resource(self):
        name = simpledialog.askstring("Resource Name", "Enter resource name (e.g. R1):", parent=self.root)
        if not name or not name.strip().isalnum():
            return
        if name in self.graph.resources or name in self.graph.processes:
            messagebox.showerror("Error", "Name already exists.", parent=self.root)
            return
        try:
            instances = int(simpledialog.askstring("Resource Instances", "How many instances?", parent=self.root))
            if instances <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Instances must be a positive integer.", parent=self.root)
            return
        self.graph.add_resource(name, instances)
        self.graph.update_after_resource_add(name)
        self.layout_nodes()
        self.status.config(text=f"Added Resource {name} ({instances})")

    def add_process(self):
        name = simpledialog.askstring("Process Name", "Enter process name (e.g. P1):", parent=self.root)
        if not name or not name.strip().isalnum():
            return
        if name in self.graph.processes or name in self.graph.resources:
            messagebox.showerror("Error", "Name already exists.", parent=self.root)
            return
        self.graph.add_process(name)
        self.layout_nodes()
        self.status.config(text=f"Added Process {name}")

    def claim_request_edge(self):
        process = simpledialog.askstring("Request Edge", "Process making request (e.g. P1):", parent=self.root)
        resource = simpledialog.askstring("Request Edge", "Resource requested (e.g. R1):", parent=self.root)
        if process not in self.graph.processes or resource not in self.graph.resources:
            messagebox.showerror("Error", "Invalid process or resource.", parent=self.root)
            return
        try:
            max_need = int(simpledialog.askstring("Max Need", f"Max number of {resource} needed by {process}:", parent=self.root))
            if max_need <= 0 or max_need > self.graph.resources[resource]['instances']:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Max need must be positive integer not exceeding resource instances.", parent=self.root)
            return
        if self.mode.get() == "Prevention":
            if not self.graph.resource_ordering_valid(process, resource):
                messagebox.showerror("Prevention Mode", "Request would violate resource ordering. Blocked!", parent=self.root)
                return
        self.graph.add_request_edge(process, resource, max_need)
        self.layout_nodes()
        self.status.config(text=f"{process} requests {resource} (max need: {max_need})")

    def assign_edge(self):
        resource = simpledialog.askstring("Assign Edge", "Resource assigned (e.g. R1):", parent=self.root)
        process = simpledialog.askstring("Assign Edge", "Assigned to Process (e.g. P1):", parent=self.root)
        if process not in self.graph.processes or resource not in self.graph.resources:
            messagebox.showerror("Error", "Invalid process or resource.", parent=self.root)
            return
        try:
            allocation = int(simpledialog.askstring("Assign", f"How many {resource} to assign to {process}?", parent=self.root))
            if allocation <= 0 or allocation > self.graph.resources[resource]['instances']:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Allocation must be a positive integer within resource instance limit.", parent=self.root)
            return

        self.graph.recalc_available()
        available = self.graph.available_vector[resource] if resource in self.graph.available_vector else self.graph.resources[resource]['instances']
        if allocation > available:
            messagebox.showerror("Assignment Error", f"Not enough available instances of {resource} to assign.", parent=self.root)
            return

        if self.mode.get() == "Avoidance":
            safe, msg = self.graph.bankers_algorithm(process, resource, allocation)
            if not safe:
                messagebox.showerror("Avoidance Mode", f"Request denied: {msg}", parent=self.root)
                return

        self.graph.add_assignment_edge(resource, process, allocation)
        self.graph.recalc_available()
        self.layout_nodes()
        self.status.config(text=f"{resource} assigned to {process} ({allocation})")

    def check_state(self):
        if self.mode.get() == "Detection":
            has_deadlock, cycles = self.graph.detect_deadlock()
            if has_deadlock:
                messagebox.showerror("Deadlock", f"System is in Deadlock!\nCycles: {cycles}", parent=self.root)
                self.status.config(text="System is in Deadlock", fg="red")
            else:
                messagebox.showinfo("No Deadlock", "System is Safe (No Deadlock detected)", parent=self.root)
                self.status.config(text="System is Safe", fg="green")
        elif self.mode.get() == "Avoidance":
            messagebox.showinfo("Avoidance Mode", "Banker's algorithm is checked during Assign. System status shown there.", parent=self.root)
        elif self.mode.get() == "Prevention":
            messagebox.showinfo("Prevention Mode", "Prevention: Resource order is enforced during requests.", parent=self.root)

    def reset(self):
        self.graph.clear()
        self.layout_nodes()
        self.status.config(text="Status: Ready", fg="blue")

    def layout_nodes(self):
        # Arrange resources at top, processes at bottom
        self.canvas.delete("all")
        width = 800
        res_y = 100
        proc_y = 380
        # Place resources
        n_res = len(self.graph.resources)
        n_proc = len(self.graph.processes)
        res_x_step = width // (n_res+1) if n_res else width
        for i, name in enumerate(self.graph.resources, 1):
            x = res_x_step*i
            y = res_y
            self.graph.node_pos[name] = (x, y)
            self.draw_node(x, y, name, "resource", self.graph.resources[name]['instances'])
        # Place processes
        proc_x_step = width // (n_proc+1) if n_proc else width
        for i, name in enumerate(sorted(self.graph.processes), 1):
            x = proc_x_step*i
            y = proc_y
            self.graph.node_pos[name] = (x, y)
            self.draw_node(x, y, name, "process")
        # Draw edges
        self.draw_edges()

    def draw_node(self, x, y, name, ntype, instances=None):
        if ntype == "resource":
            self.canvas.create_rectangle(x-NODE_RADIUS, y-NODE_RADIUS, x+NODE_RADIUS, y+NODE_RADIUS, fill="orange")
            self.canvas.create_text(x, y, text=f"{name}\n({instances})")
        else:
            self.canvas.create_oval(x-NODE_RADIUS, y-NODE_RADIUS, x+NODE_RADIUS, y+NODE_RADIUS, fill="skyblue")
            self.canvas.create_text(x, y, text=name)

    def draw_edges(self):
        # Draw request and assignment edges
        for (p, r) in self.graph.request_edges:
            if p in self.graph.node_pos and r in self.graph.node_pos:
                x1, y1 = self.graph.node_pos[p]
                x2, y2 = self.graph.node_pos[r]
                self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill="red", width=2)
        for (r, p) in self.graph.assignment_edges:
            if p in self.graph.node_pos and r in self.graph.node_pos:
                x1, y1 = self.graph.node_pos[r]
                x2, y2 = self.graph.node_pos[p]
                self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill="green", width=2)
        # Draw nodes again on top
        for name, (x, y) in self.graph.node_pos.items():
            if name in self.graph.resources:
                self.draw_node(x, y, name, "resource", self.graph.resources[name]['instances'])
            else:
                self.draw_node(x, y, name, "process")

    def show_matrices(self):
        top = Toplevel(self.root)
        top.title("Matrices")
        text = Text(top, width=70, height=22, font=("Consolas", 10))
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = Scrollbar(top, command=text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=sb.set)
        def mat_str(title, mat):
            s = f"{title}\n"
            s += "{:<8}".format("")
            for r in sorted(self.graph.resources):
                s += "{:<8}".format(r)
            s += "\n"
            for p in sorted(self.graph.processes):
                s += "{:<8}".format(p)
                for r in sorted(self.graph.resources):
                    s += "{:<8}".format(mat[p][r])
                s += "\n"
            return s
        text.insert(tk.END, mat_str("MAX Matrix", self.graph.max_matrix) + "\n")
        text.insert(tk.END, mat_str("ALLOCATION Matrix", self.graph.allocation_matrix) + "\n")
        text.insert(tk.END, mat_str("NEED Matrix", self.graph.need_matrix) + "\n")
        text.insert(tk.END, "AVAILABLE Vector\n")
        for r in sorted(self.graph.resources):
            text.insert(tk.END, f"{r}: {self.graph.available_vector.get(r, self.graph.resources[r]['instances'])}\n")
        text.config(state=tk.DISABLED)
        top.transient(self.root)
        top.grab_set()
        top.focus()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
