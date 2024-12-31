import pathlib
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog

import cv2
import numpy as np
from PIL import Image, ImageTk



class Window(ttk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.master.geometry('600x400')
        self.pack(fill=tk.BOTH, expand=True)
        self.master.bind('<Escape>', lambda event: self.master.destroy())
        self.create_ui()

        self.start_pt = None

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

        self.alpha_var = tk.StringVar()
        self.alpha_var.set('50.0')
        alpha_entry = ttk.Entry(frame, width=10, textvariable=self.alpha_var)
        alpha_entry.pack(side=tk.LEFT, padx=(2, 50))

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open', command=self.open_file)
        file_menu.add_command(label='Save', command=self.save_file)

    def click(self, event):
        scale = float(self.var_scale.get())
        x = int(event.x / (1 + scale / 100))
        y = int(event.y / (1 + scale / 100))
        if x <= self.size[0] and y <= self.size[1]:
            self.start_pt = (x, y)
            print('click', self.start_pt)

    def release(self, event):
        if self.start_pt:
            scale = float(self.var_scale.get())
            x = int(event.x / (1 + scale / 100))
            y = int(event.y / (1 + scale / 100))

            x = self.size[0] if y > self.size[0] else y
            y = self.size[1] if x > self.size[1] else x
            self.end_pt = (x, y)
            print('release', self.end_pt)
            self.draw_rectangle()

        self.start_pt = None

    def draw_rectangle(self):
        # self.img_rgb[self.start_pt[0]: self.end_pt[0] + 1, self.start_pt[1]: self.end_pt[1] + 1] = [255, 0, 0]
        self.img_rgb[self.start_pt[1]: self.end_pt[1] + 1, self.start_pt[0]: self.end_pt[0] + 1] = [255, 0, 0]
        # ndarrayのshape(行, 列)は、座標x, yと逆。
        self.img_pil = Image.fromarray(self.img_rgb)
        self.resize_img(self.var_scale.get())
        # arr[self.start_pt.x: self.end_pt.x + 1, self.start_pt.y: self/]

    def open_file(self):
        file_type = [('image file', '*.png;*.jpg')]
        init_dir = pathlib.Path(__file__).parent

        if file_path := tk.filedialog.askopenfilename(
                filetypes=file_type, initialdir=init_dir):
            print(file_path)
            self.show_image(file_path)

    def save_file(self):
        file_type = [('image file', '*.png;*.jpg')]
        init_dir = pathlib.Path(__file__).parent

        if file_path := tk.filedialog.asksaveasfilename(
                filetypes=file_type, initialdir=init_dir):
            print(file_path)
            self.save_image(file_path)

    def show_image(self, file_path):
        img_bgr = cv2.imread(file_path)
        self.img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        self.size = self.img_rgb.shape
        self.img_pil = Image.fromarray(self.img_rgb)
        # self.img_pil = Image.open(file_path)
        self.size = self.img_pil.size
        self.img_tk = ImageTk.PhotoImage(self.img_pil)
        self.canvas_id = self.canvas.create_image(0, 0, image=self.img_tk, anchor=tk.NW)

    def save_image(self, file_path):
        pass

    def resize_img(self, str_scale):
        scale = float(str_scale)
        x = int((1 + scale / 100) * self.size[0])
        y = int((1 + scale / 100) * self.size[1])
        img_resize = self.img_pil.resize((x, y))
        img_tk = ImageTk.PhotoImage(img_resize)

        self.canvas.itemconfig(self.canvas_id, image=img_tk)
        self.img_tk = img_tk


if __name__ == '__main__':
    root = tk.Tk()
    app = Window(master=root)
    app.mainloop()