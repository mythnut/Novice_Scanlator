# import the following libraries
# will convert the image to text string
from distutils.command.config import config
from fnmatch import translate
import io
import os
from tkinter import filedialog
import pytesseract

# adds image processing capabilities
from PIL import Image as ig, ImageTk, ImageDraw,ImageFont

# translates into the mentioned language
from googletrans import Translator

# adds gui functionality
import tkinter as tk
from tkinter import *
from tkinter.ttk import *

import json

import glob

# todo: figure out how to fit these into the class/package-and-module/script paradigm

def runOcr(img2, inversion,vertical,threshold):
    # path where the tesseract module is installed
    pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
    custom_config = r'-l jpn+eng --psm 6'
    if vertical == True:
        custom_config = r'-l jpn_vert --psm 5'
    result = pytesseract.image_to_string(make_ocr_ready(img2,inversion,threshold), config=custom_config)
    # write text in a text file and save it to source path
    with open('abc.rtf', mode='w', encoding="utf-16") as file:
        file.write(result)
        print(result)
    return result

def make_ocr_ready(img,inversion,threshold):
    # make the image greyscale, then apply a threshold
    img = img.convert('L')
    # if we want to invert this image, it's done here
    # this is copied code; I understand it fully
    if inversion == True:
        img = img.point(lambda p: 0 if p > (255-threshold) else 255)
    else:
        img = img.point(lambda p: 255 if p > threshold else 0)
    return img


def translateResult(result):
    p = Translator()
    # translates the text into english language
    k = p.translate(result, dest='english', src='japanese')
    return k.text


class SelectionItem():
    # todo: docstrings consisting mostly of apologies and excuses
    def __init__(self):
        self.coords = (0, 0, 0, 0)
        self.ocr_output = ""
        self.inversion = False
        self.vertical = False
        self.threshold = 127
        self.translation = ""
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)


class Model():
    """
    All the data
    todo: this makes clear that this thing is fundamentally poorly defined. fix it!
    
    Attributes
    ----------
    paths : list[str]
        description goes here
    selection_item_data : dict[str, list[SelectionItem]]
        description goes here
    json_conversion_data : dict
        description goes here
    select_opts : dict[str, tuple[Literal[2], Literal[2]] | str]
        description goes here

    Methods
    -------
    add_row(path)
        description goes here

    delete_row(path, row_index)
        description goes here
    
    save_file()
        description goes here

    startup_check()
        description goes here
    """
    # todo: find out what the right way to define attributes/properties is
    def __init__(self):
        self.paths = sorted(glob.glob('*.png'))
        self.selection_item_data = {
            path:
            [SelectionItem()]
            for path in self.paths}
        self.json_conversion_data = {}
        self.select_opts = dict(dash=(2, 2), fill='magenta', stipple='gray25', outline='black', disabledoutline='white',
                                disabledfill='white', disabledstipple='gray12', state=tk.DISABLED, tags='selection')

    # run ocr

    def add_row(self, path):
        """Adds a selection item to the data for the current item's path
        todo: fix this description!

        Parameters
        ----------
        path: str
            the file path corresponding to the currently loaded image
            todo: fix this description too!

        Side Effects
        ------------
            adds an entry to selection_item_data
        """
        self.selection_item_data[path].append(SelectionItem())

    def delete_row(self, path, row_index):
        """Deletes an entry from selection_item_data,
        for the current file path and specified row_index
        
        Parameters
        ----------
        path: str
            the file path corresponding to the currently loaded image
        
        row_index: int
            the index identifying the item to be deleted
            
        Side Effects
        ------------
            removes an entry from selection_item_data
            """
        del self.selection_item_data[path][row_index]

    def save_file(self):
        """First transfers the contents of selection_item_data to a json
        serializable type. Then dumps that to a json file.

        Side Effects
        ------------
        The value of json_conversion_data is changed.

        """
        self.json_conversion_data.clear()
        for path in self.paths:
            path_data = []
            for s in self.selection_item_data[path]:
                path_data.append({"coords":s.coords,"ocr_output":s.ocr_output,"inversion":s.inversion,"vertical":s.vertical,"threshold":s.threshold,"translation":s.translation})
            self.json_conversion_data[path] = path_data
        with io.open('json_data.json', 'w',encoding="utf-16")  as outfile:
            json.dump(self.json_conversion_data, outfile, ensure_ascii=False)

    # startup check
    def startup_check(self):
        """
        Checks for and loads a json file with saved data
        
        Side Effects
        ------------
            The value of selection_item_data is changed
            The value of json_conversion_data is changed
        """
        if os.path.isfile('json_data.json') and os.access('json_data.json', os.R_OK):
            # checks if file exists
            print("File exists and is readable")
            with io.open('json_data.json', 'r', encoding="utf-16") as infile:
                self.json_conversion_data.update(json.load(infile))
                for path in self.paths:
                    selection_items = []
                    if path in self.json_conversion_data.keys():
                        self.selection_item_data[path].clear()
                        for s in self.json_conversion_data[path]:
                            temp = SelectionItem()
                            temp.coords = s["coords"]
                            temp.ocr_output = s["ocr_output"]
                            temp.inversion = s["inversion"]
                            temp.vertical = s["vertical"]
                            temp.threshold = s["threshold"]
                            temp.translation = s["translation"]
                            selection_items.append(temp)
                        self.selection_item_data[path] = selection_items
        else:
            print("Either file is missing or is not readable, creating file...")
            self.save_file()


class View(Frame):
    """
    The GUI widgets and GUI-specific methods
    
    Attributes
    ----------
    mouse_down_x: IntVar
        the x coordinate of the starting position of a
        click-and-drag action.
    
    mouse_down_y: IntVar
        the y coordinate of the starting position of a
        click-and-drag action.

    px: IntVar
        the x coordinate of the upper left corner of the
        currently active selection box

    py: IntVar
        the y coordinate of the upper left corner of the
        currently active selection box

    sx: IntVar
        the width of the currently active selection box

    sy: IntVar
        the height of the currently active selection box

    rects: list[tuple[int, int, int, int]]
        a list of sets of coordinates for all selection
        boxes for the current image

    selection_index: int
        the index of the currently active selection box

    Methods
    -------
    scroll_start(path)
        description goes here

    scroll_move(path, row_index)
        description goes here
    
    select_start()
        description goes here

    select_move()
        description goes here

    do_popup()
        description goes here
    
    refresh_current_selection()
        description goes here
    
    change_current_selection()
        description goes here
    """
    def __init__(self, parent):
        super().__init__(parent)

        # create widgets
        # canvas
        # note - width and height settings are placeholders
        self.frame = tk.Frame(parent)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.canvas = Canvas(self.frame, width=1400, height=800)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.pack(side="top", fill=tk.BOTH)

        # side panel
        self.sidepanel = SidePanel(parent)

        # set the menu
        self.menubar = Menu(parent)

        # file submenu
        self.file = Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label='File', menu=self.file)
        # edit submenu
        self.edit = Menu(self.menubar, tearoff=False)
        self.menubar.add_cascade(label='Edit', menu=self.edit)

        # file commands
        self.file.add_command(label='Save')
        self.file.add_command(label='Open')
        self.file.add_command(label='Next File')
        self.file.add_command(label='Previous File')

        # edit commands
        self.edit.add_command(label='Add Selection')
        self.edit.add_command(label='Delete Selection')
        self.edit.add_command(label='Run Ocr')
        self.edit.add_command(label='Run Translation')
        self.edit.add_command(label='Preview Export')
        self.edit.add_command(label='Export')

        # right click menu
        self.right_click_menu = Menu(parent, tearoff=False)

        # right click commands
        self.right_click_menu.add_command(label='Add Selection')
        self.right_click_menu.add_command(label='Delete Selection')
        self.right_click_menu.add_command(label='Run Ocr')
        self.right_click_menu.add_command(label='Run Translation')
        self.right_click_menu.add_command(label='Preview Export')
        self.right_click_menu.add_command(label='Export')

        parent.config(menu=self.menubar)

        self.mouse_down_x = IntVar(value=0)
        self.mouse_down_y = IntVar(value=0)
        self.px = IntVar(value=0)
        self.py = IntVar(value=0)
        self.sx = IntVar(value=0)
        self.sy = IntVar(value=0)

        self.boxes = []
        self.selection_index = 0

        self.canvas.bind("<ButtonPress-2>", self.scroll_start)
        self.canvas.bind("<B2-Motion>", self.scroll_move)

        self.canvas.bind("<ButtonPress-1>", self.select_start)
        self.canvas.bind("<B1-Motion>", self.select_move)

    def scroll_start(self, event):
        """
        Bound to middle mouse button down. 
        Part 1 of panning the canvas with middle mouse button.
        
        Parameters
        ----------
        event: (todo: fill this in)
            the middle mouse button down event, the
            coordinates of which are to be remembered
        """
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        """
        Bound to middle mouse button held down. 
        Part 2 of panning the canvas with middle mouse button.
        
        Parameters
        ----------
        event: (todo: fill this in)
            the middle mouse button held down event, the
            coordinates of which are used to drag the canvas

        Side Effects
        ------------
            The position of the canvas is changed
        """
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def select_start(self, event):
        """
        Bound to left mouse button down. 
        Part 1 of clicking-and-dragging to position a box
        
        Parameters
        ----------
        event: (todo: fill this in)
            the left mouse button down event, the
            coordinates of which are to be remembered
        
        Side Effects
        -----------
            The values of px, mouse_down_x, py and
            mouse_down_y are changed
        """
        self.px.set(self.canvas.canvasx(event.x))
        self.mouse_down_x.set(self.canvas.canvasx(event.x))
        self.py.set(self.canvas.canvasy(event.y))
        self.mouse_down_y.set(self.canvas.canvasy(event.y))

    def select_move(self, event):
        """
        Bound to left mouse button held down. 
        Part 2 of clicking-and-dragging to position a box.
        
        Parameters
        ----------
        event: (todo: fill this in)
            the left mouse button held down event, the
            coordinates of which are used to set the
            box's bounds

        Side Effects
        -----------
            The values of px, sx, py and sy are changed
        """
        self.px.set(min(self.mouse_down_x.get(), self.canvas.canvasx(event.x)))
        self.sx.set(abs(self.mouse_down_x.get()-self.canvas.canvasx(event.x)))
        self.py.set(min(self.mouse_down_y.get(), self.canvas.canvasy(event.y)))
        self.sy.set(abs(self.mouse_down_y.get()-self.canvas.canvasy(event.y)))
        self.redraw_active_box()
    
    def do_popup(self,event):
        """
        open right click menu

        Parameters
        ----------
        event: (todo: fill this in)
            the right click event, the coordinates of
            which are used to position the menu
        """
        try:
            self.right_click_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.right_click_menu.grab_release()

    def redraw_active_box(self):
        """
        redraw the currently active box

        Side Effects
        ------------
            A canvas item is changed.
        """
        self.canvas.coords(self.boxes[self.selection_index],self.px.get(),self.py.get(),self.px.get() + self.sx.get(),self.sy.get()+self.py.get())
    
    def change_active_box(self, new_index):
        """
        switches the active box to be the one at
        the specified index

        Parameters
        ----------
        new_index: int
            the index of the box to make active

        Side EFfects
        ------------
            selection_index is changed
            the selection of selection_list is changed
            the resources of one or two canvas items
            are configured
            px, sx, py, and sy are changed
        """
        if self.selection_index < self.sidepanel.selection_list.size():
            self.canvas.itemconfigure(self.boxes[self.selection_index], state=tk.DISABLED)
        self.selection_index = min(self.sidepanel.selection_list.size() - 1, new_index)
        self.sidepanel.selection_list.selection_set(self.selection_index)
        self.canvas.itemconfigure(self.boxes[self.selection_index], state=tk.NORMAL)
        x0,y0,x1,y1 = self.canvas.coords(self.boxes[self.selection_index])
        self.px.set(x0)
        self.sx.set(x1-x0)
        self.py.set(y0)
        self.sy.set(y1-y0)


class SidePanel():
    """
    The GUI widgets and GUI-specific methods
    
    Attributes
    ----------
    inversion: IntVar
        description goes here
    
    vertical: IntVar
        description goes here

    threshold: IntVar
        description goes here
    """
    def __init__(self, root):
        # containing frame
        self.frame2 = tk.Frame(root)
        self.frame2.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # checkbuttons frame
        self.frame3 = tk.Frame(self.frame2)
        self.frame3.pack(side="top",fill=tk.BOTH)

        # inversion checkbutton
        self.inversion = IntVar()
        self.inversion_checkbutton = tk.Checkbutton(
            self.frame3, variable = self.inversion, text='Invert', onvalue=True, offvalue=False)
        self.inversion_checkbutton.pack(side=tk.LEFT, fill=tk.BOTH)

        # vertical text checkbutton
        self.vertical = IntVar()
        self.vertical_checkbutton = tk.Checkbutton(
            self.frame3, variable = self.vertical, text='Vertical', onvalue=True, offvalue=False)
        self.vertical_checkbutton.pack(side=tk.LEFT, fill=tk.BOTH)

        # ocr area
        self.ocr_area = Text(self.frame2, height=5, width=50)
        self.ocr_area.pack(side="top", fill=tk.BOTH)

        # translation area
        self.translation_area = Text(self.frame2, height=5, width=50)
        self.translation_area.pack(side="top", fill=tk.BOTH)

        # selection list
        self.selection_list = Listbox(
            self.frame2, selectmode='single', exportselection=False)
        self.selection_list.pack(side="top", fill=tk.BOTH)

        # canvas
        self.canvas = Canvas(self.frame2, width=400, height=200)
        self.canvas.pack(side="top", fill=tk.BOTH)

        # threshold slider
        self.threshold = IntVar()
        self.threshold_slider = tk.Scale( self.frame2, variable = self.threshold,orient='horizontal', from_ = 0, to = 254)
        self.threshold_slider.pack(side="top", fill=tk.BOTH)


class Controller:
    """
    The GUI widgets and GUI-specific methods
    
    Attributes
    ----------
    path: str
        description goes here

    Methods
    -------
    on_listbox_select()
        description goes here

    add_selection()
        description goes here
    
    delete_selection()
        description goes here

    update_gui_with_file_data(path)
        description goes here

    load_selection_data(path, selection_index)
        description goes here
    
    set_ocr_output(ocr_output)
        description goes here
    
    set_translation(translation)
        description goes here

    set_rects(path)
        description goes here

    get_file_path_by_open_file_dialog()
        description goes here
    
    open_image_file_by_path(pathArg)
        description goes here

    next_file(path)
        description goes here

    prev_file()
        description goes here
    
    select_end()
        description goes here
    
    update_model_inversion()
        description goes here
    
    update_model_vertical()
        description goes here

    run_ocr_button_clicked()
        description goes here

    run_translation_button_clicked()
        description goes here
    
    crop_image()
        description goes here

    update_sidepanel_image()
        description goes here

    preview_export_button_clicked()
        description goes here
    
    export_button_clicked(event)
        description goes here
    """
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Tkinter MVC Demo')
        self.path = ""
        self.model = Model()
        self.model.startup_check()
        self.view = View(self.root)
        self.view.sidepanel.selection_list.bind(
            '<<ListboxSelect>>', self.on_listbox_select)
        self.view.sidepanel.inversion.trace_add('write',self.update_model_inversion)
        self.view.sidepanel.vertical.trace_add('write',self.update_model_vertical)
        self.view.file.entryconfig(0, command=self.model.save_file)
        self.view.file.entryconfig(1, command=lambda: self.open_image_file_by_path(
            self.get_file_path_by_open_file_dialog()))
        self.view.file.entryconfig(2, command=self.next_file)
        self.view.file.entryconfig(3, command=self.prev_file)
        self.view.edit.entryconfig(0, command=self.add_selection)
        self.view.edit.entryconfig(1, command=self.delete_selection)
        self.view.edit.entryconfig(2, command=self.run_ocr_button_clicked)
        self.view.edit.entryconfig(3, command=self.run_translation_button_clicked)
        self.view.edit.entryconfig(4, command=self.preview_export_button_clicked)
        self.view.edit.entryconfig(5, command=self.export_button_clicked)
        self.view.canvas.bind("<ButtonRelease-1>", self.select_end)
        self.view.canvas.bind("<Button-3>", self.view.do_popup)
        self.view.sidepanel.threshold.trace_add('write',self.update_sidepanel_image)
        self.view.right_click_menu.entryconfig(0, command=self.add_selection)
        self.view.right_click_menu.entryconfig(1, command=self.delete_selection)
        self.view.right_click_menu.entryconfig(2, command=self.run_ocr_button_clicked)
        self.view.right_click_menu.entryconfig(3, command=self.run_translation_button_clicked)
        self.view.right_click_menu.entryconfig(4, command=self.preview_export_button_clicked)
        self.view.right_click_menu.entryconfig(5, command=self.export_button_clicked)
        self.open_image_file_by_path(self.get_file_path_by_open_file_dialog())

    # On Listbox Select
    # controls which selection box is active
    def on_listbox_select(self, event):
        w = event.widget
        self.view.change_active_box(w.curselection()[0])
        self.load_selection_data(self.path,w.curselection()[0])

    # Add Selection
    def add_selection(self):
        self.model.add_row(self.path)
        self.update_gui_with_file_data(self.path)

    # Delete Selection
    def delete_selection(self):
        self.model.delete_row(self.path,self.view.selection_index)
        self.update_gui_with_file_data(self.path)

    # Update GUI With File Data
    # should feed data for a given file from the model to the view
    # so when you switch files or edit data, this should refresh the GUI
    def update_gui_with_file_data(self, path):
        # refresh all selection boxes
        self.set_rects(path)

        # refresh list of selection boxes
        self.view.sidepanel.selection_list.delete(0,self.view.sidepanel.selection_list.size() - 1)
        for i in range(len(self.model.selection_item_data[path])):
            self.view.sidepanel.selection_list.insert(tk.END,str(i))

        self.view.change_active_box(self.view.sidepanel.selection_list.size())
        # refresh the inversion checkbutton and ocr area
        if(len(self.model.selection_item_data[path]) > 0):
            self.load_selection_data(path, self.view.selection_index)
        else:
            self.view.sidepanel.ocr_area.delete("1.0", END)
            self.view.sidepanel.translation_area.delete("1.0",END)
            self.view.sidepanel.inversion.set(False)
            self.view.sidepanel.vertical.set(False)
            self.view.sidepanel.threshold.set(127)

    # Load Selection Data
    # should be what keeps the ocr string and inversion boolean synchronized between model and view
    def load_selection_data(self, path, selection_index):
        self.set_ocr_output(self.model.selection_item_data[path][selection_index].ocr_output)
        self.set_translation(self.model.selection_item_data[path][selection_index].translation)
        self.view.sidepanel.inversion.set(int(self.model.selection_item_data[path][selection_index].inversion))
        self.view.sidepanel.vertical.set(int(self.model.selection_item_data[path][selection_index].vertical))
        self.view.sidepanel.threshold.set(self.model.selection_item_data[path][selection_index].threshold)
        self.update_sidepanel_image()

    # Set OCR Output
    # to refresh the contents of the optical character recognition output text area with the right data
    def set_ocr_output(self, ocr_output):
        self.view.sidepanel.ocr_area.delete("1.0", END)
        self.view.sidepanel.ocr_area.insert(END, ocr_output)

    # Set Translation
    # to refresh the contents of the translation text area with the right data
    def set_translation(self, translation):
        self.view.sidepanel.translation_area.delete("1.0", END)
        self.view.sidepanel.translation_area.insert(END, translation)

    # Set Rects
    # part of loading files
    def set_rects(self, path):
        self.view.boxes.clear()
        self.view.canvas.delete('selection')
        for i in self.model.selection_item_data[path]:
            self.view.boxes.append(self.view.canvas.create_rectangle(
                i.coords[0], i.coords[1], i.coords[2], i.coords[3], **self.model.select_opts))

    # Get File Path By Open File Dialog
    # shows an open file dialog, and returns the path to the selected
    # file in a format that's ready for opening the file.
    # only handles the dialog and formatting the path string
    def get_file_path_by_open_file_dialog(self):
        pathArg = filedialog.askopenfilename(title="Select Image", filetypes=(
            ("png files", ".png"), ("jpeg files", ".jpg")))
        split_path = pathArg.split("/")
        return split_path[len(split_path) - 1]

    # Open Image File By Path
    # opens an image file and calls all necessary subsequent operations
    def open_image_file_by_path(self, pathArg):
        # update the current file path in "state"
        self.path = pathArg

        # open the new image
        self.image = ig.open(pathArg)
        img = ImageTk.PhotoImage(self.image)
        self.view.canvas.create_image(
            0, 0, image=img, anchor=tk.NW, tag="img1")
        self.view.canvas.img = img  # Keep reference.
        
        # reset canvas dimensions
        self.view.canvas.configure(width=img.width(), height=img.height(
        ), scrollregion=self.view.canvas.bbox("all"))

        # update_gui_with_file_data refreshes all GUI 
        self.update_gui_with_file_data(pathArg)
        
    def next_file(self):
        path_index = self.model.paths.index(self.path)
        self.open_image_file_by_path(self.model.paths[(path_index+1)%len(self.model.paths)])
    def prev_file(self):
        path_index = self.model.paths.index(self.path)
        if path_index == 0:
            self.open_image_file_by_path(self.model.paths[len(self.model.paths) - 1])
        else:
            self.open_image_file_by_path(self.model.paths[path_index - 1])

    def select_end(self, event):
        self.model.selection_item_data[self.path][self.view.selection_index].coords = (self.view.px.get(),self.view.py.get(),self.view.px.get()+self.view.sx.get(),self.view.py.get()+self.view.sy.get())
        self.crop_image()
    
    def update_model_inversion(self,varname=None, idx=None, mode=None):
        self.model.selection_item_data[self.path][self.view.selection_index].inversion=bool(self.view.sidepanel.inversion.get())
    
    def update_model_vertical(self,varname=None, idx=None, mode=None):
        self.model.selection_item_data[self.path][self.view.selection_index].vertical=bool(self.view.sidepanel.vertical.get())

    def run_ocr_button_clicked(self,event=None):
        self.crop_image()
        
    def run_translation_button_clicked(self,event=None):
        ocr_output = self.view.sidepanel.ocr_area.get("1.0",END)
        self.model.selection_item_data[self.path][self.view.selection_index].ocr_output=ocr_output
        self.view.sidepanel.translation_area.delete("1.0",END)
        if ocr_output != '':
            translation = translateResult(ocr_output)
            self.model.selection_item_data[self.path][self.view.selection_index].translation = translation
            self.view.sidepanel.translation_area.insert(END,translation)
        
    def crop_image(self):
        img2 = self.image.crop([self.view.px.get(),self.view.py.get(),self.view.px.get()+self.view.sx.get(),self.view.py.get()+self.view.sy.get()])
        ocr_output = runOcr(img2,self.model.selection_item_data[self.path][self.view.selection_index].inversion,self.model.selection_item_data[self.path][self.view.selection_index].vertical,self.view.sidepanel.threshold.get())
        self.model.selection_item_data[self.path][self.view.selection_index].ocr_output=ocr_output
        self.view.sidepanel.ocr_area.delete("1.0",END)
        self.view.sidepanel.ocr_area.insert(END,ocr_output)
        self.view.sidepanel.translation_area.delete("1.0",END)
        if ocr_output != '':
            translation = translateResult(ocr_output)
            self.model.selection_item_data[self.path][self.view.selection_index].translation = translation
            self.view.sidepanel.translation_area.insert(END,translation)
        self.model.selection_item_data[self.path][self.view.selection_index].threshold = self.view.sidepanel.threshold.get()
        self.update_sidepanel_image()

    def update_sidepanel_image(self,varname=None, idx=None, mode=None):
        # open the new image
        img2 = self.image.crop([self.view.px.get(),self.view.py.get(),self.view.px.get()+self.view.sx.get(),self.view.py.get()+self.view.sy.get()])
        img = ImageTk.PhotoImage(make_ocr_ready(img2,self.model.selection_item_data[self.path][self.view.selection_index].inversion,self.view.sidepanel.threshold.get()))
        self.view.sidepanel.canvas.create_image(
            0, 0, image=img, anchor=tk.NW, tag="img1")
        self.view.sidepanel.canvas.img = img  # Keep reference.

    def preview_export_button_clicked(self,event=None):
        select_opts = dict(fill='white', stipple='', width=0, state=tk.NORMAL,tags='backing')
        self.view.boxes.clear()
        self.view.canvas.delete('selection')
        for i in self.model.selection_item_data[self.path]:
            self.view.canvas.create_rectangle(i.coords[0], i.coords[1], i.coords[2], i.coords[3], **select_opts)
            self.view.canvas.create_text((i.coords[0] + i.coords[2])/2,(i.coords[1]+ i.coords[3])/2,text=i.translation,tags='translation')

    def export_button_clicked(self,event=None):
        image1 = self.image.copy()
        draw = ImageDraw.Draw(image1)
        select_opts = dict(fill='white', stipple='', width=0, state=tk.NORMAL,tags='backing')
        for i in self.model.selection_item_data[self.path]:
            draw.rectangle([(i.coords[0], i.coords[1]), (i.coords[2], i.coords[3])], fill='white', width=0)
            draw.text((i.coords[0],i.coords[1]),text=i.translation,font=ImageFont.truetype("arial"),fill='black')
        image1.save('output/' + self.path.replace('.png','_translated.png'))

if __name__ == '__main__':
    c = Controller()
    c.root.mainloop()