import pathlib
import tkinter as tk
import tkinter.ttk as ttk
# import tkinter.filedialog
from tkinter import messagebox, filedialog
from typing import NamedTuple


import cv2
import numpy as np
from PIL import Image, ImageTk


class Size(NamedTuple):

    rows: int
    cols: int
    color: int = None

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

        self.create_ui()
        # img_bgr = cv2.imread('test_images/top_ground_src2.png')
        # img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        # img_pil = Image.fromarray(img_rgb)
        # self.img_tk = ImageTk.PhotoImage(img_pil)
        # size = img_bgr.shape
        # # import pdb; pdb.set_trace()
        # # self.canvas = tk.Canvas(self, width=size[0], height=size[1])  #, background="white")
        # self.canvas = tk.Canvas(self)  #, background="white")
        # self.canvas.pack(fill=tk.BOTH, expand=True)
        # self.canvas.create_image(0, 0, image=self.img_tk, anchor=tk.NW)

    def create_ui(self):
        # base_frame = ttk.Frame(self)
        # base_frame.pack(fill=tk.BOTH, expand=True)
        self.create_display_area()
        self.create_widget_area()
        self.create_menu()

    def create_display_area(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('<Button1-Motion>', self.mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)

    def create_widget_area(self):
        frame = ttk.Frame(self)
        frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        label = tk.Label(frame, text='size', width=2)
        label.pack(side=tk.LEFT, padx=(50, 2))

        self.var_scale = tk.DoubleVar()
        self.var_scale.set(0)
        size_slider = ttk.Scale(frame, from_=0, to=100, length=200, variable=self.var_scale, command=self.resize_img)
        size_slider.pack(side=tk.LEFT, padx=(5, 50), pady=(6, 1))

        label = ttk.Label(frame, text='alpha')
        label.pack(side=tk.LEFT, padx=(2, 2))

        self.alpha_var = tk.StringVar(value=str(self.default_alpha))
        # self.alpha_var.set(str(self.default_alpha))
        alpha_entry = ttk.Entry(
            frame,
            width=10,
            textvariable=self.alpha_var
        )
        alpha_entry.pack(side=tk.LEFT, padx=(2, 50))

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open', command=self.open)
        file_menu.add_command(label='Save', command=self.save)

    def click(self, event):
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
                tag='temp_rect'
            )

    def mouse_drag(self, event):
        x, y = self.scaled_size.replace_outside_pt(event)
        self.canvas.coords('temp_rect', self.start_pt.x, self.start_pt.y, x, y)

    def release(self, event):
        if self.start_pt:
            self.canvas.delete('temp_rect')
            scale = self.scaled_size.rows / self.size.rows
            pt0 = self.start_pt.get_original_pt(scale)

            x, y = self.scaled_size.replace_outside_pt(event)
            end_pt = Point(x, y)
            pt1 = end_pt.get_original_pt(scale)

            x0, x1 = min(pt0.x, pt1.x), max(pt0.x, pt1.x)
            y0, y1 = min(pt0.y, pt1.y), max(pt0.y, pt1.y)

            self.img_rgb[y0: y1 + 1, x0: x1 + 1] = [0, 255, 0]
            # self.img_rgb[self.start_pt[1]: self.end_pt[1] + 1, self.start_pt[0]: self.end_pt[0] + 1] = [0, 255, 0]
            # ndarrayのshape(行, 列)は、座標x, yと逆。
            self.img_pil = Image.fromarray(self.img_rgb)
            self.resize_img(self.var_scale.get())

        self.start_pt = None

    def draw_rectangle(self):
        self.img_rgb[self.start_pt[1]: self.end_pt[1] + 1, self.start_pt[0]: self.end_pt[0] + 1] = [0, 255, 0]
        # ndarrayのshape(行, 列)は、座標x, yと逆。
        self.img_pil = Image.fromarray(self.img_rgb)
        self.resize_img(self.var_scale.get())
        # arr[self.start_pt.x: self.end_pt.x + 1, self.start_pt.y: self/]

    def open(self):
        file_type = [('image file', '*.png;*.jpg')]
        init_dir = pathlib.Path(__file__).parent

        if file_path := filedialog.askopenfilename(
                filetypes=file_type, initialdir=init_dir):
            print(file_path)
            self.show_image(file_path)

    def save(self):
        file_type = [('image file', '*.png;*.jpg')]
        init_dir = pathlib.Path(__file__).parent

        if file_path := filedialog.asksaveasfilename(
                filetypes=file_type, initialdir=init_dir):
            print(file_path)
            self.save_image(file_path)

    def show_image(self, file_path):
        self.img_bgr = cv2.imread(file_path)
        self.size = Size(*self.img_bgr.shape)
        print(self.size)
        # import pdb; pdb.set_trace()
        # code = cv2.COLOR_BGRA2RGBA if self.size.color == 4 else cv2.COLOR_BGR2RGB
        # self.img_rgb = cv2.cvtColor(self.img_bgr, code)
        self.img_rgb = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB)
        # self.size = Size(*self.img_rgb.shape)
        self.img_pil = Image.fromarray(self.img_rgb)
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
                self.img_bgr = np.insert(self.img_bgr, 3, 255, axis=2)

            for i in range(self.size[1]):
                for j in range(self.size[0]):
                    arr = self.img_rgb[i, j]
                    if arr[0] == 0 and arr[1] == 255 and arr[2] == 0:
                        self.img_bgr[i, j][3] = alpha

            cv2.imwrite(file_path, self.img_bgr)

    def resize_img(self, str_scale):
        scale = float(str_scale)
        rows, cols = self.size.scale(1 + scale / 100)
        # x = int((1 + scale / 100) * self.size[0])
        # y = int((1 + scale / 100) * self.size[1])
        img_resize = self.img_pil.resize((cols, rows))
        img_tk = ImageTk.PhotoImage(img_resize)

        self.canvas.itemconfig(self.canvas_id, image=img_tk)
        self.img_tk = img_tk


if __name__ == '__main__':
    root = tk.Tk()
    app = Window(master=root)
    app.mainloop()