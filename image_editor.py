import pathlib
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
from typing import NamedTuple

import cv2
import numpy as np
from PIL import Image, ImageTk


class CannotReadImageFile(Exception):
    pass


class Size(NamedTuple):

    rows: int
    cols: int
    color: int = None
    mode: int = None

    def __len__(self):
        return len([v for v in self if v is not None])

    def scale(self, scale):
        return int(self.rows * scale), int(self.cols * scale)

    def is_inside(self, pt):
        if pt.x <= self.cols and pt.y <= self.rows:
            return True

    def replace_outside_pt(self, pt):
        x = self.cols if pt.x > self.cols else pt.x
        y = self.rows if pt.y > self.rows else pt.y
        return x, y


class Point(NamedTuple):

    x: int
    y: int

    def get_original_pt(self, scale):
        org_x = int(self.x / scale)
        org_y = int(self.y / scale)
        return Point(org_x, org_y)


class Window(ttk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.master.geometry('600x400')
        self.pack(fill=tk.BOTH, expand=True)
        self.master.bind('<Escape>', lambda event: self.master.destroy())

        self.start_pt = None
        self.default_alpha = 50
        self.img_tk = None
        self.rect_tag = 'temp_rect'
        self.is_edit = False

        self.create_ui()

    def create_ui(self):
        self.create_display_area()
        self.create_widget_area()
        self.create_menu()

    def create_display_area(self):
        frame = ttk.Frame(self, relief=tk.SUNKEN)
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(frame, bg='#D3D3D3')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('<Button1-Motion>', self.mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)

    def create_widget_area(self):
        frame = ttk.Frame(self, relief=tk.SUNKEN, padding=(10, 20))
        frame.pack(side=tk.BOTTOM, fill=tk.BOTH)

        label = ttk.Label(frame, text='size')
        label.pack(side=tk.LEFT, padx=(10, 2))

        self.var_scale = tk.DoubleVar(value=0)
        size_slider = ttk.Scale(
            frame,
            from_=0,
            to=100,
            length=400,
            variable=self.var_scale,
            command=self.resize_img
        )
        size_slider.pack(side=tk.LEFT, padx=(2, 5))

        label = ttk.Label(frame, text='alpha')
        label.pack(side=tk.LEFT, padx=(10, 2))

        self.alpha_var = tk.StringVar(value=str(self.default_alpha))
        alpha_entry = ttk.Entry(
            frame,
            width=10,
            textvariable=self.alpha_var
        )
        alpha_entry.pack(side=tk.LEFT, padx=(2, 10))

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open', command=self.open, accelerator="Ctrl+O")
        file_menu.add_command(label='Save', command=self.save, accelerator="Ctrl+S")

        edit_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Undo', command=self.change_cursor, accelerator="Ctrl+Z")

        self.bind_all("<Control-z>", self.change_cursor)
        self.bind_all("<Control-o>", self.open)
        self.bind_all("<Control-s>", self.save)

    def click(self, event):
        if self.img_tk:
            scale = float(self.var_scale.get())
            self.scaled_size = Size(*self.size.scale(1 + scale / 100))

            if self.scaled_size.is_inside(event):
                self.start_pt = Point(event.x, event.y)

                self.canvas.create_rectangle(
                    self.start_pt.x,
                    self.start_pt.y,
                    self.start_pt.x + 1,
                    self.start_pt.y + 1,
                    outline='#00FF00',
                    width=2,
                    tag=self.rect_tag
                )

    def mouse_drag(self, event):
        if self.start_pt:
            x, y = self.scaled_size.replace_outside_pt(event)
            self.canvas.coords(self.rect_tag, self.start_pt.x, self.start_pt.y, x, y)

    def release(self, event):
        if self.start_pt:
            self.canvas.delete(self.rect_tag)
            scale = self.scaled_size.rows / self.size.rows
            pt0 = self.start_pt.get_original_pt(scale)

            x, y = self.scaled_size.replace_outside_pt(event)
            end_pt = Point(x, y)
            pt1 = end_pt.get_original_pt(scale)

            x0, x1 = min(pt0.x, pt1.x), max(pt0.x, pt1.x)
            y0, y1 = min(pt0.y, pt1.y), max(pt0.y, pt1.y)

            if self.is_edit:
                self.undo(x0, y0, x1, y1)
            else:
                self.draw(x0, y0, x1, y1)

            self.start_pt = None

    def open(self, event=None):
        file_type = [('image', '*.png;*.jpg')]
        init_dir = pathlib.Path(__file__).parent

        if file_path := filedialog.askopenfilename(
                filetypes=file_type, initialdir=init_dir):
            print(file_path)
            self.show_image(file_path)

    def save(self, event=None):
        if self.img_tk:
            file_type = [('image', '*.png')]
            init_dir = pathlib.Path(__file__).parent

            if file_path := filedialog.asksaveasfilename(
                    filetypes=file_type, initialdir=init_dir):
                print(file_path)
                self.save_image(file_path)

    def read(self, file_path):
        try:
            mode = cv2.IMREAD_UNCHANGED
            if (img := cv2.imread(file_path, mode)) is None:
                raise CannotReadImageFile()

        except CannotReadImageFile:
            messagebox.showwarning(
                "Alert", "Can't open/read file: check file path/integrity.")
            return None, None
        else:
            if len(size := img.shape) == 3 and size[2] == 4:
                return img, mode

            return cv2.imread(file_path), cv2.IMREAD_COLOR

    def show_image(self, file_path):
        self.img_org, mode = self.read(file_path)

        if self.img_org is not None:
            self.var_scale.set(0)
            self.size = Size(*self.img_org.shape, mode=mode)

            code = cv2.COLOR_BGRA2RGBA if self.size.color == 4 else cv2.COLOR_BGR2RGB
            self.img_cvt = cv2.cvtColor(self.img_org, code)
            self.img_pil = Image.fromarray(self.img_cvt)
            self.img_tk = ImageTk.PhotoImage(self.img_pil)
            self.canvas_id = self.canvas.create_image(0, 0, image=self.img_tk, anchor=tk.NW)

    def validate_alpha(self):
        try:
            alpha = int(self.alpha_var.get())
            return min(alpha, 255)
        except ValueError:
            messagebox.showwarning(
                "Alert", "Enter a positive integer to alpha field.")
            return None

    def save_image(self, file_path):
        if (alpha := self.validate_alpha()) is not None:
            if self.size.color == 3:
                self.img_org = np.insert(self.img_org, 3, 255, axis=2)
                self.size = self.size._replace(color=4)

            for i in range(self.size.rows):
                for j in range(self.size.cols):
                    arr = self.img_cvt[i, j]
                    if arr[0] == 0 and arr[1] == 255 and arr[2] == 0:
                        self.img_org[i, j][3] = alpha

            cv2.imwrite(file_path, self.img_org)

    def resize_img(self, str_scale):
        if self.img_tk:
            scale = float(str_scale)
            rows, cols = self.size.scale(1 + scale / 100)

            img_resize = self.img_pil.resize((cols, rows))
            img_tk = ImageTk.PhotoImage(img_resize)
            self.canvas.itemconfig(self.canvas_id, image=img_tk)
            self.img_tk = img_tk

    def change_cursor(self, event=None):
        if self.img_tk:
            self.canvas.configure(cursor='plus')
            self.is_edit = True

    def draw(self, x0, y0, x1, y1):
        color = [0, 255, 0, 255] if self.size.mode == cv2.IMREAD_UNCHANGED else [0, 255, 0]
        self.img_cvt[y0: y1 + 1, x0: x1 + 1] = color
        self.img_pil = Image.fromarray(self.img_cvt)
        self.resize_img(self.var_scale.get())

    def undo(self, x0, y0, x1, y1):
        if self.size.color == 4:
            self.img_org[y0: y1 + 1, x0: x1 + 1, 3] = 255

        self.img_cvt[y0: y1 + 1, x0: x1 + 1] = self.img_org[y0: y1 + 1, x0: x1 + 1]
        self.img_pil = Image.fromarray(self.img_cvt)
        self.resize_img(self.var_scale.get())
        self.canvas.configure(cursor='arrow')
        self.is_edit = False


if __name__ == '__main__':
    root = tk.Tk()
    app = Window(master=root)
    app.mainloop()