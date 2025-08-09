import tkinter as tk
from tkinter import ttk
import json

# Load the JSON data
with open("justin_jefferson_2022.json", "r") as f:
    player_data = json.load(f)

# Recursive function to insert JSON into the tree
def insert_items(parent, dictionary):
    if isinstance(dictionary, dict):
        for key, value in dictionary.items():
            node_id = tree.insert(parent, 'end', text=key, open=False)
            insert_items(node_id, value)
    elif isinstance(dictionary, list):
        for idx, item in enumerate(dictionary):
            node_id = tree.insert(parent, 'end', text=f"[{idx}]", open=False)
            insert_items(node_id, item)
    else:
        tree.insert(parent, 'end', text=str(dictionary))

# Create the GUI window
root = tk.Tk()
root.title("Justin Jefferson 2022 Player Object")

tree = ttk.Treeview(root)
tree.pack(expand=True, fill='both')

# Insert root node and build the tree
root_node = tree.insert('', 'end', text='justin_jefferson_2022', open=True)
insert_items(root_node, player_data)

# Add scrollbar
scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side='right', fill='y')

# Run the GUI loop
root.mainloop()
