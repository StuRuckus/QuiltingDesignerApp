import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter import filedialog
import json
from PIL import Image

class Patch:
    def __init__(self, size, color, coords):
        self.size = size
        self.color = color
        self.coords = coords  # Coordinates of the patch

class Block:
    def __init__(self, patches):
        self.patches = patches

class QuiltDesignerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quilt Design App")

        self.patches = []
        self.stored_patches = []
        self.selected_patch = None
        self.selected_patches = []
        self.offset = (0, 0)
        self.grid_size = 50  # Size of each grid cell

        self.create_widgets()

    def create_widgets(self):
        label = tk.Label(self.root, text="Welcome to Quilt Designer")
        label.pack()

        color_picker_button = tk.Button(self.root, text="Choose Color", command=self.choose_color)
        color_picker_button.pack()

        create_patch_button = tk.Button(self.root, text="Create Patch", command=self.choose_color)
        create_patch_button.pack()

        select_patches_button = tk.Button(self.root, text="Select Stored Patches", command=self.select_stored_patches)
        select_patches_button.pack()

        group_patches_button = tk.Button(self.root, text="Group Selected Patches", command=self.group_selected_patches)
        group_patches_button.pack()

        save_project_button = tk.Button(self.root, text="Save Project", command=self.save_project)
        save_project_button.pack()

        load_project_button = tk.Button(self.root, text="Load Project", command=self.load_project)
        load_project_button.pack()

        export_image_button = tk.Button(self.root, text="Export as Image", command=self.export_as_image)
        export_image_button.pack()

        self.canvas = tk.Canvas(self.root, width=800, height=800, bg="white")
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

    def choose_color(self):
        color = askcolor()[1]

        if color:
            self.create_patch(color)

    def create_patch(self, color):
        if len(self.stored_patches) < 1000:
            size = 50

            patch = Patch(size, color, None)
            self.stored_patches.append(patch)

            self.display_patch(patch, len(self.stored_patches) - 1)
        else:
            print("You can only store up to 1000 patches.")

    def display_patch(self, patch, index):
        size = patch.size
        color = patch.color

        x, y = 10 + (index % 16) * (size + 10), 10 + (index // 16) * (size + 10)
        patch.coords = (x, y)

        rect = self.canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline=color, tags="patch")
        self.patches.append((rect, patch))

    def select_stored_patches(self):
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Stored Patches")

        patch_listbox = tk.Listbox(select_window, selectmode=tk.MULTIPLE)
        for i, patch in enumerate(self.stored_patches):
            patch_listbox.insert(i, f"Patch {i + 1}")

        patch_listbox.pack()

        use_button = tk.Button(select_window, text="Use Selected Patches",
                               command=lambda: self.use_selected_patches(patch_listbox.curselection(), select_window))
        use_button.pack()

    def use_selected_patches(self, selected_indices, select_window):
        for i in selected_indices:
            patch = self.stored_patches[i]
            self.display_patch(patch, len(self.patches))

        select_window.destroy()

    def start_drag(self, event):
        x, y = event.x, event.y
        item = self.canvas.find_closest(x, y)
        if item:
            self.selected_patch = item[0]
            self.offset = (x - self.canvas.coords(self.selected_patch)[0], y - self.canvas.coords(self.selected_patch)[1])
            self.highlight_patch(self.selected_patch)

    def drag(self, event):
        x, y = event.x, event.y
        if self.selected_patch:
            self.canvas.move(self.selected_patch, x - self.offset[0] - self.canvas.coords(self.selected_patch)[0],
                             y - self.offset[1] - self.canvas.coords(self.selected_patch)[1])

    def end_drag(self, event):
        if self.selected_patch:
            coords = self.canvas.coords(self.selected_patch)
            x, y = coords[0], coords[1]

            # Snap to the nearest grid point
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size

            self.canvas.coords(self.selected_patch, x, y, x + self.grid_size, y + self.grid_size)
            self.unhighlight_patch(self.selected_patch)
            del self.selected_patch

    def highlight_patch(self, patch):
        self.canvas.itemconfig(patch, outline="red", width=3)

    def unhighlight_patch(self, patch):
        _, patch_obj = next(p for p in self.patches if p[0] == patch)
        self.canvas.itemconfig(patch, outline=patch_obj.color, width=1)

    def group_selected_patches(self):
        if not self.selected_patches:
            return

        x_coords = []
        y_coords = []
        color = None

        for rect, patch in self.selected_patches:
            coords = self.canvas.coords(rect)
            x_coords.extend([coords[0], coords[2]])
            y_coords.extend([coords[1], coords[3]])
            color = patch.color  # Assuming all selected patches have the same color

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # Create a new patch with the bounding box of the selected patches
        new_patch_size = (max_x - min_x, max_y - min_y)
        new_patch_color = color
        new_patch = Patch(new_patch_size, new_patch_color, (min_x, min_y))

        # Draw the new patch
        self.canvas.create_rectangle(min_x, min_y, max_x, max_y, fill=new_patch_color, outline=new_patch_color, tags="patch")
        self.stored_patches.append(new_patch)

        # Remove the individual patches
        for rect, _ in self.selected_patches:
            self.canvas.delete(rect)

        self.selected_patches = []

    def save_project(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        project_data = []
        for rect, patch in self.patches:
            coords = self.canvas.coords(rect)
            project_data.append({
                "coords": coords,
                "color": patch.color,
                "size": patch.size
            })

        with open(file_path, 'w') as f:
            json.dump(project_data, f)

    def load_project(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        with open(file_path, 'r') as f:
            project_data = json.load(f)

        self.canvas.delete("all")
        self.patches = []

        for patch_data in project_data:
            coords = patch_data["coords"]
            color = patch_data["color"]
            size = patch_data["size"]

            rect = self.canvas.create_rectangle(*coords, fill=color, outline=color, tags="patch")
            patch = Patch(size, color, coords[:2])
            self.patches.append((rect, patch))

    def export_as_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if not file_path:
            return

        self.canvas.postscript(file="temp.ps", colormode='color')
        img = Image.open("temp.ps")
        img.save(file_path, "png")

def main():
    root = tk.Tk()
    app = QuiltDesignerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
