import tkinter as tk
from tkinter import messagebox
import networkx as nx
import random
import math

class HamiltonianApp:
    """
    A stable, interactive desktop application for visualizing the Hamiltonian Cycle
    problem, built from scratch using Python's standard Tkinter library.
    """
    def __init__(self, root):
        # --- Core Application State ---
        self.root = root
        self.root.title("Hamiltonian Cycle Finder")
        self.mode = 'idle'
        self.graph = nx.Graph()
        self.layout = {}
        self.selected_node = None
        
        # --- Solver and Animation State ---
        self.solver_generator = None
        self.path = []

        # --- UI Configuration ---
        self.NODE_RADIUS = 15
        self.root.config(bg='#2E2E2E')

        # --- Create UI Elements ---
        title = tk.Label(root, text="Hamiltonian Cycle Finder", font=("Helvetica", 20, "bold"), fg="#A78BFA", bg='#2E2E2E')
        title.pack(pady=10)

        self.canvas = tk.Canvas(root, width=800, height=500, bg="#111827", highlightthickness=0)
        self.canvas.pack(pady=10, padx=20)
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

        self.instructions = tk.Label(root, text="", font=("Helvetica", 12), fg="#D1D5DB", bg='#2E2E2E')
        self.instructions.pack(pady=5)

        # --- Button Frames ---
        self.idle_frame = tk.Frame(root, bg='#2E2E2E')
        self.drawing_frame = tk.Frame(root, bg='#2E2E2E')
        self.solving_frame = tk.Frame(root, bg='#2E2E2E')
        self.finished_frame = tk.Frame(root, bg='#2E2E2E')
        
        self._create_buttons()
        self._set_mode('idle')

    def _create_buttons(self):
        """Creates all the buttons for the application."""
        # Idle Buttons
        tk.Button(self.idle_frame, text="Random Graph", command=self._generate_random).pack(side=tk.LEFT, padx=10)
        tk.Button(self.idle_frame, text="Guaranteed Cycle", command=self._generate_guaranteed).pack(side=tk.LEFT, padx=10)
        tk.Button(self.idle_frame, text="Draw Graph", command=lambda: self._set_mode('drawing')).pack(side=tk.LEFT, padx=10)

        # Drawing Buttons
        tk.Button(self.drawing_frame, text="Back to Menu", command=lambda: self._set_mode('idle')).pack(side=tk.LEFT, padx=10)
        tk.Button(self.drawing_frame, text="Clear Drawing", command=self._clear_drawing).pack(side=tk.LEFT, padx=10)
        tk.Button(self.drawing_frame, text="Solve Custom Graph", command=self._solve_custom).pack(side=tk.LEFT, padx=10)

        # Solving Button
        tk.Button(self.solving_frame, text="STOP", command=self._request_stop, bg='red', fg='white').pack(pady=10)
        
        # Finished Button
        tk.Button(self.finished_frame, text="Back to Menu", command=lambda: self._set_mode('idle')).pack(pady=10)

    def _set_mode(self, mode):
        """Controls which set of buttons and instructions are visible."""
        self.mode = mode
        
        # Forget all frames
        self.idle_frame.pack_forget()
        self.drawing_frame.pack_forget()
        self.solving_frame.pack_forget()
        self.finished_frame.pack_forget()

        if self.mode == 'idle':
            self.instructions.config(text="Select a graph generation method or start drawing.")
            self.idle_frame.pack(pady=10)
            self._clear_drawing()
        elif self.mode == 'drawing':
            self.instructions.config(text="Left-click: Add/Select Node | Right-click: Delete Node")
            self.drawing_frame.pack(pady=10)
            self._clear_drawing()
        elif self.mode == 'solving':
            self.instructions.config(text="Solving... Click STOP to cancel.")
            self.solving_frame.pack(pady=10)
        elif self.mode == 'finished':
            self.finished_frame.pack(pady=10)

    def _clear_drawing(self):
        self.graph.clear(); self.layout = {}; self.selected_node = None
        self.canvas.delete("all")

    def _redraw_canvas(self):
        """Draws the current graph state onto the canvas."""
        self.canvas.delete("all")
        # Draw edges first
        for u, v in self.graph.edges():
            self.canvas.create_line(self.layout[u], self.layout[v], fill='gray', width=2)
        # Draw nodes
        for node, pos in self.layout.items():
            color = 'yellow' if node == self.selected_node else 'skyblue'
            x0, y0 = pos[0] - self.NODE_RADIUS, pos[1] - self.NODE_RADIUS
            x1, y1 = pos[0] + self.NODE_RADIUS, pos[1] + self.NODE_RADIUS
            self.canvas.create_oval(x0, y0, x1, y1, fill=color, outline='black')
            self.canvas.create_text(pos, text=str(node))

    def _on_canvas_left_click(self, event):
        if self.mode != 'drawing': return
        pos = (event.x, event.y)
        clicked_node = self._get_node_at_pos(pos)
        
        if clicked_node is not None:
            if self.selected_node is None:
                self.selected_node = clicked_node
            else:
                if self.selected_node != clicked_node: self.graph.add_edge(self.selected_node, clicked_node)
                self.selected_node = None
        else:
            new_node_id = 0
            while new_node_id in self.graph.nodes(): new_node_id += 1
            self.graph.add_node(new_node_id); self.layout[new_node_id] = pos
            self.selected_node = None
        self._redraw_canvas()

    def _on_canvas_right_click(self, event):
        if self.mode != 'drawing': return
        pos = (event.x, event.y)
        clicked_node = self._get_node_at_pos(pos)

        if self.selected_node and clicked_node and self.graph.has_edge(self.selected_node, clicked_node):
            self.graph.remove_edge(self.selected_node, clicked_node)
        elif clicked_node is not None:
            self.graph.remove_node(clicked_node)
            del self.layout[clicked_node]
        self.selected_node = None
        self._redraw_canvas()

    def _get_node_at_pos(self, pos):
        """Finds a node at a given canvas coordinate."""
        for node, node_pos in self.layout.items():
            if math.dist(pos, node_pos) < self.NODE_RADIUS:
                return node
        return None

    def _start_solving(self, graph, layout):
        if not graph.nodes():
            messagebox.showerror("Error", "Cannot solve an empty graph.")
            return
        self._set_mode('solving')
        self.graph = graph; self.layout = layout
        self.path = [list(self.graph.nodes())[0]]
        self.solver_generator = self._find_cycle_generator()
        self._solver_step() # Start the animation loop

    def _find_cycle_generator(self):
        """A generator that yields control at each step of the backtracking search."""
        if len(self.path) == len(self.graph.nodes()):
            return self.graph.has_edge(self.path[-1], self.path[0])
        yield
        last_node = self.path[-1]
        for neighbor in self.graph.neighbors(last_node):
            if neighbor not in self.path:
                self.path.append(neighbor)
                solution_found = yield from self._find_cycle_generator()
                if solution_found: return True
                self.path.pop() # Backtrack
        return False
        
    def _solver_step(self):
        """The heartbeat of the solver, driven by tkinter's after method."""
        if self.mode != 'solving': return

        try:
            next(self.solver_generator)
            self._draw_search_step()
            self.root.after(200, self._solver_step) # Schedule next step
        except StopIteration as e:
            solution_found = e.value
            self._set_mode('finished')
            if solution_found:
                self.instructions.config(text="✅ Hamiltonian Cycle Found!")
                self._draw_final_path(True)
            else:
                self.instructions.config(text="❌ No Hamiltonian Cycle exists.")
                self._draw_final_path(False)

    def _request_stop(self):
        """Instantly stops the solver and returns to the finished screen."""
        print("Stop request received!")
        self.solver_generator = None # This will stop the loop
        self._set_mode('finished')
        self.instructions.config(text="Search Stopped by User.")
        self._redraw_canvas()

    def _draw_search_step(self):
        self._redraw_canvas() # Redraws nodes
        # Draw path edges
        path_edges = [(self.path[i], self.path[i+1]) for i in range(len(self.path) - 1)]
        for u, v in path_edges:
            self.canvas.create_line(self.layout[u], self.layout[v], fill='blue', width=3)

    def _draw_final_path(self, is_success):
        self._redraw_canvas()
        if is_success:
            path_edges = [(self.path[i], self.path[i+1]) for i in range(len(self.path) - 1)]
            path_edges.append((self.path[-1], self.path[0])) # Closing edge
            for u, v in path_edges:
                self.canvas.create_line(self.layout[u], self.layout[v], fill='green', width=4)

    # --- Button Callbacks ---
    def _generate_random(self):
        g = nx.erdos_renyi_graph(7, 0.6)
        pos_dict = nx.spring_layout(g, scale=200, center=(400, 250))
        self._start_solving(g, {k: tuple(v) for k, v in pos_dict.items()})

    def _generate_guaranteed(self):
        num_v = 7; g = nx.Graph()
        nodes = list(range(num_v)); random.shuffle(nodes)
        g.add_nodes_from(nodes)
        for i in range(num_v): g.add_edge(nodes[i], nodes[(i + 1) % num_v])
        for i in range(num_v):
            for j in range(i + 1, num_v):
                if not g.has_edge(nodes[i], nodes[j]) and random.random() < 0.3: g.add_edge(nodes[i], nodes[j])
        pos_dict = nx.spring_layout(g, scale=200, center=(400, 250))
        self._start_solving(g, {k: tuple(v) for k, v in pos_dict.items()})

    def _solve_custom(self):
        self._start_solving(self.graph.copy(), self.layout)

if __name__ == "__main__":
    # You need to have networkx installed: pip install networkx
    root = tk.Tk()
    app = HamiltonianApp(root)
    root.mainloop()