# import the following libraries
from enum import Enum
import io
from json import tool
import os
import re

# will convert the image to text string
import pytesseract
from pytesseract import Output

# adds image processing capabilities
from PIL import Image as ig, ImageTk, ImageDraw, ImageFont

# translates into the mentioned language
from googletrans import Translator

# adds GUI functionality
import tkinter as tk
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

import json

import glob


def run_ocr(img: Image, is_inverted: bool, is_vertical: bool, threshold: int) -> str:
    """
    Applies various settings, then calls pytesseract.image_to_string

    Parameters
    ----------
    img: Image
        an image containing text to be scanned

    is_inverted: bool
        whether to invert the values of the image

    is_vertical : bool
        whether the text being scanned is printed vertically

    threshold: int
        the threshold value for converting the image to black and white
    """
    # path where the tesseract module is installed
    pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
    custom_config = r'-l jpn+eng --psm 6'
    if is_vertical == True:
        custom_config = r'-l jpn_vert --psm 5'
    ocr_output = pytesseract.image_to_string(make_ocr_ready(
        img, is_inverted, threshold), config=custom_config)
    return ocr_output


def make_ocr_ready(img: Image, is_inverted: bool, threshold: int) -> Image:
    """
    Processes the raw image to ensure optimal results from ocr

    Parameters
    ----------
    img: Image
        an image containing text to be scanned

    is_inverted: bool
        whether to invert the values of the image

    threshold: int
        the threshold value for converting the image to black and white
    """
    # make the image greyscale, then apply a threshold
    img = img.convert('L')
    # if we want to invert this image, it's done here
    if is_inverted == True:
        img = img.point(lambda p: 0 if p > (255-threshold) else 255)
    else:
        img = img.point(lambda p: 255 if p > threshold else 0)
    return img


def get_translation(untranslated_text: str) -> str:
    """
    Translates text in Japanese to English

    Parameters
    ----------
    untranslated_text: str
        text obtained by ocr, in the source language
    """
    p = Translator()
    # translates the text into english language
    translator_output = p.translate(
        untranslated_text, dest='english', src='japanese')
    return translator_output.text


class SelectionItem():
    """
    Represents the data of a single selection box

    Attributes
    ----------
    coords : tuple[int, int, int, int]
        coordinates of the selection box

    ocr_output : str
        the result of scanning the text in the image

    is_inverted : bool
        whether to invert the values of the image

    is_vertical : bool
        whether the text being scanned is printed vertically

    threshold: int
        the threshold value for converting the image to black and white

    translation: str
        the translated text

    Methods
    -------
    to_json()
        returns all data in json serializable form
    """
    # TODO: docstrings consisting mostly of apologies and excuses

    def __init__(self):
        self.coords = (0, 0, 0, 0)
        self.ocr_output = ""
        self.is_inverted = False
        self.is_vertical = False
        self.threshold = 127
        self.translation = ""

    def to_json(self):
        """
        Returns all data in json serializable form
        """
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class ToolType(Enum):
    SELECT = 0
    ADD = 1
    CROP = 2
    DELETE = 3
    JOIN = 4
    SPLIT = 5
    TRANSFORM = 6


class Model():
    """
    All the data

    Attributes
    ----------
    paths : list[str]
        list of image file paths in source directory

    selection_item_data : dict[str, list[SelectionItem]]
        all application data for all image files in source directory

    select_opts : dict[str, tuple[int, int] | str]
        the display options for selection boxes in the GUI

    Methods
    -------
    add_row(path)
        adds a selection box to data

    delete_row(path, row_index)
        deletes a selection box from data

    save_file(source_directory)
        saves data to json file

    startup_check(source_directory)
        loads data from file or creates data and file if no file exists
    """

    def __init__(self):
        self.paths = []
        self.unsaved_changes = False
        self.select_opts = dict(dash=(2, 2), fill='magenta', stipple='gray25', outline='black', disabledoutline='blue',
                                disabledfill='blue', disabledstipple='gray12', state=tk.DISABLED, tags='selection')

    def set_directory(self, path: str):
        allfiles = glob.glob(path + '/*')
        paths = []
        for file in allfiles:
            if re.search(r'.+\.(png|jpg|jpeg)', file):
                split_file = file.split("\\")
                paths.append(split_file[split_file.__len__() - 1])
        self.paths = sorted(paths)
        self.selection_item_data = {
            path:
            [SelectionItem()]
            for path in self.paths}

    def add_row(self, path: str):
        """
        Adds a selection box to the data for the current image file

        Parameters
        ----------
        path: str
            the file path corresponding to the currently loaded image

        Side Effects
        ------------
            adds an entry to selection_item_data
        """
        self.selection_item_data[path].append(SelectionItem())

    def delete_row(self, path: str, row_index: int):
        """
        Deletes an entry from selection_item_data,
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

    def save_file(self, source_directory: str):
        """
        First transfers the contents of selection_item_data to a json
        serializable type. Then dumps that to a json file.

        Parameters
        ----------
        source_directory: str
            the path of the directory containing all the files to be translated

        Side Effects
        ------------
            the value of the json save file is changed
        """
        json_conversion_data = {}
        for path in self.paths:
            # TODO: skip if no data
            path_data = []
            for s in self.selection_item_data[path]:
                path_data.append({"coords": s.coords, "ocr_output": s.ocr_output, "is_inverted": s.is_inverted,
                                 "is_vertical": s.is_vertical, "threshold": s.threshold, "translation": s.translation})
            json_conversion_data[path] = path_data
        with io.open(source_directory + "/json-data.json", 'w', encoding="utf-16") as outfile:
            json.dump(json_conversion_data, outfile, ensure_ascii=False)
        self.unsaved_changes = False

    def startup_check(self, source_directory: str):
        """
        Checks for and loads a json file with saved data

        Parameters
        ----------
        source_directory: str
            the path of the directory containing all the files to be translated

        Side Effects
        ------------
            * The value of selection_item_data is changed
            * If json-data.json doesn't exist in the source directory, it is
            created
        """
        if os.path.isfile(source_directory + "/json-data.json") and os.access(source_directory + "/json-data.json", os.R_OK):
            # checks if file exists
            print("File exists and is readable")
            with io.open(source_directory + "/json-data.json", 'r', encoding="utf-16") as infile:
                json_conversion_data = {}
                json_conversion_data.update(json.load(infile))
                for path in self.paths:
                    # all the image files in the source directory
                    selection_items = []
                    if path in json_conversion_data.keys():
                        # json-data.json has data for this image file
                        self.selection_item_data[path].clear()
                        # having cleared out any old data, load in the new
                        for selection_item in json_conversion_data[path]:
                            temp = SelectionItem()
                            temp.coords = selection_item["coords"]
                            temp.ocr_output = selection_item["ocr_output"]
                            temp.is_inverted = selection_item["is_inverted"]
                            temp.is_vertical = selection_item["is_vertical"]
                            temp.threshold = selection_item["threshold"]
                            temp.translation = selection_item["translation"]
                            selection_items.append(temp)
                        self.selection_item_data[path] = selection_items
        else:
            print("Either file is missing or is not readable, creating file...")


class View(Frame):
    """
    The GUI widgets and GUI-specific methods

    Attributes
    ----------
    canvas: Canvas
        TODO

    menubar: Menu
        TODO

    right_click_menu: Menu
        TODO

    sidepanel: SidePanel
        TODO

    mouse_down_x: IntVar
        the x coordinate of the starting position of a
        click-and-drag action.

    mouse_down_y: IntVar
        the y coordinate of the starting position of a
        click-and-drag action.

    box_x_position: IntVar
        the x coordinate of the upper left corner of the
        currently active selection box

    box_y_position: IntVar
        the y coordinate of the upper left corner of the
        currently active selection box

    box_width: IntVar
        the width of the currently active selection box

    box_height: IntVar
        the height of the currently active selection box

    box_ids: list[int]]
        a list of canvas Ids all selection
        boxes for the current image

    selection_index: int
        the index of the currently active selection box

    Methods
    -------
    scroll_start(event)
        saves the coordinates of a middle-mouse-click as part
        of enabling scrolling the canvas

    scroll_move(event)
        gets the current mouse coordinates as part
        of enabling scrolling the canvas

    select_start(event)
        saves the coordinates of a left-click as part
        of placing selection boxes

    select_move(event)
        gets the current mouse coordinates as part
        of placing selection boxes

    do_popup(event)
        shows the right click menu

    redraw_active_box()
        redraws the active selection box

    change_active_box(new_index)
        chooses a different active selection box
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
        self.edit.add_command(label='Export')

        # right click menu
        self.right_click_menu = Menu(parent, tearoff=False)

        # right click commands
        self.right_click_menu.add_command(label='Add Selection')
        self.right_click_menu.add_command(label='Delete Selection')
        self.right_click_menu.add_command(label='Run Ocr')
        self.right_click_menu.add_command(label='Run Translation')
        self.right_click_menu.add_command(label='Export')

        parent.config(menu=self.menubar)

        # canvas panning bindings
        self.canvas.bind("<ButtonPress-2>", self.scroll_start)
        self.canvas.bind("<B2-Motion>", self.scroll_move)

        # variables
        # selection box dragging variables
        self.mouse_down_x = IntVar(value=0)
        self.mouse_down_y = IntVar(value=0)
        # selection box coordinate variables
        self.box_x_position = IntVar(value=0)
        self.box_y_position = IntVar(value=0)
        self.box_width = IntVar(value=0)
        self.box_height = IntVar(value=0)
        # box ids
        self.box_ids = []
        # index of active box
        self.selection_index = 0

    def scroll_start(self, event: Event):
        """
        Bound to middle mouse button down. 
        Part 1 of panning the canvas with middle mouse button.

        Parameters
        ----------
        event: Event
            the middle mouse button down event, the
            coordinates of which are to be remembered
        """
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event: Event):
        """
        Bound to middle mouse button held down. 
        Part 2 of panning the canvas with middle mouse button.

        Parameters
        ----------
        event: Event
            the middle mouse button held down event, the
            coordinates of which are used to drag the canvas

        Side Effects
        ------------
            The position of the canvas is changed
        """
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def do_popup(self, event: Event):
        """
        open right click menu

        Parameters
        ----------
        event: Event
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
        x0 = self.box_x_position.get()
        y0 = self.box_y_position.get()
        x1 = self.box_x_position.get() + self.box_width.get()
        y1 = self.box_height.get()+self.box_y_position.get()
        self.canvas.coords(self.selection_box_id, x0, y0, x1, y1)
        self.canvas.tag_raise(self.selection_box_id,self.image_id)

    def change_active_box(self, new_index: int):
        """
        switches the active box to be the one at
        the specified index

        Parameters
        ----------
        new_index: int
            the index of the box to make active

        Side EFfects
        ------------
            * selection_index is changed
            * the selection of selection_list is changed
            * the resources of one or two canvas items
            are configured
            * box_x_position, box_width, box_y_position, and box_height are changed
        """
        if self.selection_index < self.sidepanel.selection_list.size():
            self.canvas.itemconfigure(
                self.box_ids[self.selection_index], state=tk.DISABLED)
        self.selection_index = min(
            self.sidepanel.selection_list.size() - 1, new_index)
        self.sidepanel.selection_list.selection_set(self.selection_index)
        self.canvas.itemconfigure(
            self.box_ids[self.selection_index], state=tk.NORMAL)
        x0, y0, x1, y1 = self.canvas.coords(self.box_ids[self.selection_index])
        self.box_x_position.set(x0)
        self.box_width.set(x1-x0)
        self.box_y_position.set(y0)
        self.box_height.set(y1-y0)


class SidePanel():
    """
    The widgets pertaining to the current selection

    Attributes
    ----------
    checkbuttons_frame: tk.Frame
        the inner frame containing the checkbuttons

    is_inverted: IntVar
        the value of the is_inverted checkbox widget

    is_inverted_checkbutton: tk.Checkbutton
        the checkbutton that controls is_inverted

    is_vertical: IntVar
        the value of the is_inverted checkbox widget

    is_vertical_checkbutton: tk.Checkbutton
        the checkbutton that controls is_vertical

    ocr_area: Text
        the text area that shows the OCR captured text

    translation_area: Text
        the text area that shows the translated text

    selection_list: Listbox
        the listbox that contains the selection boxes for the current image

    preview_image: Canvas
        the canvas that previews the current selection converted to
        black and white according to the threshold

    threshold_slider: tk.Scale
        the slider that controls threshold

    threshold: IntVar
        the value of the threshold slider widget

    run_ocr_button: Button
        the button for manually running OCR

    run_translation_button: Button
        the button for manually running translation

    export_button: Button
        the button for exporting
    """

    def __init__(self, root):
        # containing frame
        self.frame = tk.Frame(root)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # checkbuttons frame
        self.checkbuttons_frame = tk.Frame(self.frame)
        self.checkbuttons_frame.pack(side="top", fill=tk.BOTH)

        # is_inverted checkbutton
        self.is_inverted = IntVar()
        self.is_inverted_checkbutton = tk.Checkbutton(
            self.checkbuttons_frame, variable=self.is_inverted, text='Invert', onvalue=True, offvalue=False)
        self.is_inverted_checkbutton.pack(side=tk.LEFT, fill=tk.BOTH)

        # is_vertical text checkbutton
        self.is_vertical = IntVar()
        self.vertical_checkbutton = tk.Checkbutton(
            self.checkbuttons_frame, variable=self.is_vertical, text='Vertical', onvalue=True, offvalue=False)
        self.vertical_checkbutton.pack(side=tk.LEFT, fill=tk.BOTH)

        # ocr area
        self.ocr_area = Text(self.frame, height=5, width=50)
        self.ocr_area.pack(side="top", fill=tk.BOTH)

        # translation area
        self.translation_area = Text(self.frame, height=5, width=50)
        self.translation_area.pack(side="top", fill=tk.BOTH)

        # selection list
        self.selection_list = Listbox(
            self.frame, selectmode='single', exportselection=False)
        self.selection_list.pack(side="top", fill=tk.BOTH)

        # canvas
        self.preview_image = Canvas(self.frame, width=400, height=200)
        self.preview_image.pack(side="top", fill=tk.BOTH)

        # threshold slider
        self.threshold = IntVar()
        self.threshold_slider = tk.Scale(
            self.frame, variable=self.threshold, orient='horizontal', from_=0, to=254)
        self.threshold_slider.pack(side="top", fill=tk.BOTH)

        # run ocr button
        self.run_ocr_button = Button(self.frame, text="Run OCR")
        self.run_ocr_button.pack(side="top", fill=tk.BOTH)

        # run translation button
        self.run_translation_button = Button(
            self.frame, text="Run Translation")
        self.run_translation_button.pack(side="top", fill=tk.BOTH)

        # export button
        self.export_button = Button(self.frame, text="Export")
        self.export_button.pack(side="top", fill=tk.BOTH)

        # toggle display mode button
        self.toggle_display_mode_button = Button(
            self.frame, text="Toggle Display Mode")
        self.toggle_display_mode_button.pack(side="top", fill=tk.BOTH)

        # get bounding boxes button
        self.get_bounding_boxes_button = Button(
            self.frame, text="Get Bounding Boxes")
        self.get_bounding_boxes_button.pack(side="top", fill=tk.BOTH)

        # tool type label
        self.tool_type_label = Label(self.frame)
        self.tool_type_label.pack(side="top", fill=tk.BOTH)


class Controller:
    """
    The GUI widgets and GUI-specific methods

    Attributes
    ----------
    model: Model
        a model, which holds data

    view: View
        a view, which has the GUI

    source_directory: str
        path of source directory

    path: str
        file path of current open image

    Methods
    -------
    on_listbox_select(event)
        enables switching the active selection box by clicking an item
        in the listbox widget

    add_selection()
        adds a selection box

    delete_selection()
        deletes a selection box

    update_gui_with_file_data(path)
        loads data and updates GUI

    load_selection_data(path, selection_index)
        updates the view widgets with data from current selection box

    set_ocr_output(ocr_output)
        sets the contents of the ocr_output text area widget

    set_translation(translation)
        sets the contents of the translation text area widget

    set_boxes(path)
        draws all the selection boxes for the current image file

    get_file_path_by_open_file_dialog()
        shows an open file dialog and returns the path

    open_image_file_by_path(path)
        opens an image file by its file path

    next_file()
        opens the next file

    prev_file()
        opens the previous file

    select_end()
        ends the click-and-drag for placing a selection box

    update_is_inverted_data()
        updates the model with changed is_inverted data

    update_is_vertical_data()
        updates the model with changed is_vertical data

    run_ocr_button_clicked()
        runs ocr when the button is clicked

    run_translation_button_clicked()
        runs translation when the button is clicked

    crop_image()
        gets an image cropped to the selection box bounds and runs ocr

    update_preview_image()
        updates the preview of the text to be scanned

    export_button_clicked(event)
        exports a translated image when the button is clicked
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Novice Scanlator App')
        self.path = ""
        self.display_mode = "box"
        # choose source directory
        self.source_directory = filedialog.askdirectory(
            title="Select Directory")
        # create model
        self.model = Model()
        # set directory
        self.model.set_directory(self.source_directory)
        # load data if it exists
        self.model.startup_check(self.source_directory)
        # create view
        self.view = View(self.root)

        # sidepanel variable bindings
        self.view.sidepanel.selection_list.bind(
            '<<ListboxSelect>>', self.on_listbox_select)
        self.view.sidepanel.is_inverted.trace_add(
            'write', self.update_is_inverted_data)
        self.view.sidepanel.is_vertical.trace_add(
            'write', self.update_is_vertical_data)
        self.view.sidepanel.threshold.trace_add(
            'write', self.update_preview_image)

        # sidepanel widget bindings
        self.view.sidepanel.run_ocr_button.bind(
            '<Button-1>', self.run_ocr_button_clicked)
        self.view.sidepanel.run_translation_button.bind(
            '<Button-1>', self.run_translation_button_clicked)
        self.view.sidepanel.export_button.bind(
            '<Button-1>', self.export_button_clicked)
        self.view.sidepanel.toggle_display_mode_button.bind(
            '<Button-1>', self.toggle_display_mode_button_clicked)
        self.view.sidepanel.get_bounding_boxes_button.bind(
            '<Button-1>', self.get_bounding_boxes_button_clicked)

        # file menu command bindings
        self.view.file.entryconfig(
            0, command=lambda: self.model.save_file(self.source_directory))
        self.view.file.entryconfig(1, command=lambda: self.open_image_file_by_path(
            self.get_file_path_by_open_file_dialog()))
        self.view.file.entryconfig(2, command=self.next_file)
        self.view.file.entryconfig(3, command=self.prev_file)

        # edit menu command bindings
        self.view.edit.entryconfig(0, command=self.add_selection)
        self.view.edit.entryconfig(1, command=self.delete_selection)
        self.view.edit.entryconfig(2, command=self.run_ocr_button_clicked)
        self.view.edit.entryconfig(
            3, command=self.run_translation_button_clicked)
        self.view.edit.entryconfig(5, command=self.export_button_clicked)

        # right click menu bindings
        self.view.right_click_menu.entryconfig(0, command=self.add_selection)
        self.view.right_click_menu.entryconfig(
            1, command=self.delete_selection)
        self.view.right_click_menu.entryconfig(
            2, command=self.run_ocr_button_clicked)
        self.view.right_click_menu.entryconfig(
            3, command=self.run_translation_button_clicked)
        self.view.right_click_menu.entryconfig(
            5, command=self.export_button_clicked)

        # additional canvas mouse click bindings
        self.view.canvas.bind("<ButtonPress-1>", self.select_start)
        self.view.canvas.bind("<B1-Motion>", self.select_move)
        self.view.canvas.bind("<ButtonRelease-1>", self.select_end)
        self.view.canvas.bind("<Button-3>", self.view.do_popup)

        # tool type
        self.tool_type = ToolType.SELECT
        self.view.sidepanel.tool_type_label.configure(text=self.tool_type.name)
        self.root.bind('e', lambda event: self.next_tool_type())
        self.root.bind('q', lambda event: self.prev_tool_type())
        self.root.bind('<Tab>', self.next_file_hotkey)
        self.root.bind('<Shift-Tab>', self.prev_file_hotkey)
        self.root.bind('<Control-s>', lambda event: self.model.save_file())
        self.root.bind('a', lambda event: self.set_tool_type(ToolType.ADD))
        self.root.bind('s', lambda event: self.set_tool_type(ToolType.SELECT))
        self.root.bind('d', lambda event: self.set_tool_type(ToolType.DELETE))
        self.root.bind('f', lambda event: self.set_tool_type(ToolType.JOIN))
        self.root.bind('z', lambda event: self.set_tool_type(ToolType.TRANSFORM))
        self.root.bind('x', lambda event: self.set_tool_type(ToolType.SPLIT))
        self.root.bind('c', lambda event: self.set_tool_type(ToolType.CROP))
        self.view.canvas.bind("<Motion>",self.update_cursor)

        self.transform_move = False
        (self.transform_x0,self.transform_y0,self.transform_x1,self.transform_y1) = (False,False,False,False)
        self.remember_coords = (0,0,0,0)
        self.transform_offset = (0,0)



        # open file
        self.open_image_file_by_path(self.get_file_path_by_open_file_dialog())

        select_opts = dict(dash=(2, 2), fill='magenta', stipple='gray25', outline='black', disabledoutline='blue',
                                disabledfill='blue', disabledstipple='gray12', state=tk.DISABLED, tags='tool')
        self.view.selection_box_id = self.view.canvas.create_rectangle((0,0,0,0),**select_opts)

    def update_cursor(self, event):
        canvas_x = self.view.canvas.canvasx(event.x)
        canvas_y = self.view.canvas.canvasy(event.y)
        # TODO: make collision box larger
        boxes = list(set(self.view.canvas.find_overlapping(canvas_x,canvas_y,canvas_x,canvas_y)).intersection(set(self.view.box_ids)))
        if len(boxes) > 0 and self.tool_type == ToolType.TRANSFORM:
            box = self.model.selection_item_data[self.path][self.get_data_index_from_box_id(
            boxes[0])].coords
            if (canvas_x - box[0] <= 10 and canvas_y - box[1] <= 10) or (box[2] - canvas_x <= 10 and box[3] - canvas_y <= 10):
                self.view.canvas.config(cursor="@downright_upleft_double_arrow.cur")
            elif (canvas_x - box[0] <= 10 and box[3] - canvas_y <= 10) or (box[2] - canvas_x <= 10 and canvas_y - box[1] <= 10):
                self.view.canvas.config(cursor="@upright_downleft_double_arrow.cur")
            elif canvas_x - box[0] <= 10 or box[2] - canvas_x <= 10:
                self.view.canvas.config(cursor="@horizontal_double_arrow.cur")
            elif canvas_y - box[1] <= 10 or box[3] - canvas_y <= 10:
                self.view.canvas.config(cursor="@up_down_double_arrow.cur")
            else:
                self.view.canvas.config(cursor="fleur")
        else:
            self.view.canvas.config(cursor="arrow")

    def next_file_hotkey(self, event: None):
        self.next_file()
        return 'break'
        
    def prev_file_hotkey(self, event: None):
        self.prev_file()
        return 'break'

    def on_listbox_select(self, event: Event):
        """
        When an item is clicked in the view's selection list widget,
        calls view.change_active_box and load_selection_data to
        activate the selected item.

        Parameters
        ----------
        event: Event
            the item click event

        Side Effects
        ------------
            * calls view.change_active_box and load_selection_data,
            * updating the view's widgets and variables
        """
        w = event.widget
        self.view.change_active_box(w.curselection()[0])
        self.load_selection_data(self.path, w.curselection()[0])

    def add_selection(self):
        """
        Adds a new selection box for the current image

        Side Effects
        ------------
            calls model.add_row and update_gui_with_file_data,
            adding an entry to model.selection_item_data
            and updating the sidebar's selection list
        """
        self.model.add_row(self.path)
        self.update_gui_with_file_data(self.path)

    def delete_selection(self):
        """
        Deletes the selection box for the current image
        at the current index

        Side Effects
        ------------
            calls model.delete_row and update_gui_with_file_data,
            removing an entry from model.selection_item_data
            and updating the sidebar's selection list
        """
        self.model.delete_row(self.path, self.view.selection_index)
        self.update_gui_with_file_data(self.path)

    def update_gui_with_file_data(self, path: str):
        """
        Gets data for given file path from model.
        Updates view widgets with that data.

        Parameters
        ----------
        path: str
            the file path for the image to be loaded

        Side Effects
        ------------
            The view's widgets are updated
        """
        # refresh all selection boxes
        self.set_boxes(path)

        # refresh list of selection boxes
        self.view.sidepanel.selection_list.delete(
            0, self.view.sidepanel.selection_list.size() - 1)
        for i in range(len(self.model.selection_item_data[path])):
            self.view.sidepanel.selection_list.insert(tk.END, str(i))
        # set the active box
        self.view.change_active_box(self.view.sidepanel.selection_list.size())

        # refresh the remaining sidepanel widgets
        if(len(self.model.selection_item_data[path]) > 0):
            self.load_selection_data(path, self.view.selection_index)
        else:
            self.view.sidepanel.ocr_area.delete("1.0", END)
            self.view.sidepanel.translation_area.delete("1.0", END)
            self.view.sidepanel.is_inverted.set(False)
            self.view.sidepanel.is_vertical.set(False)
            self.view.sidepanel.threshold.set(127)

    def load_selection_data(self, path: str, selection_index: int):
        """
        Gets data for given selection box to switch to.
        Updates view widgets with that data.

        Parameters
        ----------
        path: str
            the file path for the currently loaded image

        selection_index: int
            the index of the selection box to be switched to

        Side Effects
        ------------
            The view's widgets are updated
        """
        self.set_ocr_output(
            self.model.selection_item_data[path][selection_index].ocr_output)
        self.set_translation(
            self.model.selection_item_data[path][selection_index].translation)
        self.view.sidepanel.is_inverted.set(
            int(self.model.selection_item_data[path][selection_index].is_inverted))
        self.view.sidepanel.is_vertical.set(
            int(self.model.selection_item_data[path][selection_index].is_vertical))
        self.view.sidepanel.threshold.set(
            self.model.selection_item_data[path][selection_index].threshold)
        self.update_preview_image()

    def set_ocr_output(self, ocr_output: str):
        """
        Updates the view's ocr area with new text.

        Parameters
        ----------
        ocr_output: str
            the new text to populate the ocr area

        Side Effects
        ------------
            The ocr area is updated
        """
        self.view.sidepanel.ocr_area.delete("1.0", END)
        self.view.sidepanel.ocr_area.insert(END, ocr_output)

    def set_translation(self, translation: str):
        """
        Updates the view's translation area with new text.

        Parameters
        ----------
        translation: str
            the new text to populate the translation area

        Side Effects
        ------------
            The translation area is updated
        """
        self.view.sidepanel.translation_area.delete("1.0", END)
        self.view.sidepanel.translation_area.insert(END, translation)

    def set_boxes(self, path: str):
        """
        Loads selection box data for a given image file.

        Parameters
        ----------
        path: str
            the file path for the specified image

        Side Effects
        ------------
            * The canvas is updated
            * view.boxes is updated
        """
        self.view.box_ids.clear()
        self.view.canvas.delete('selection')
        if self.display_mode == "box":
            for i in self.model.selection_item_data[path]:
                self.view.box_ids.append(self.view.canvas.create_rectangle(
                    i.coords[0], i.coords[1], i.coords[2], i.coords[3], **self.model.select_opts))
        else:
            select_opts = dict(fill='white', stipple='',
                               width=0, state=tk.NORMAL, tags='selection')
            for i in self.model.selection_item_data[path]:
                self.view.box_ids.append(self.view.canvas.create_rectangle(
                    i.coords[0], i.coords[1], i.coords[2], i.coords[3], **select_opts))
                self.view.canvas.create_text(
                    (i.coords[0] + i.coords[2])/2, (i.coords[1] + i.coords[3])/2, text=i.translation, tags='selection', font=('Arial', '12'), width=i.coords[2]-i.coords[0])

    def get_file_path_by_open_file_dialog(self) -> str:
        """
        Shows an open file dialog and returns the path to the selected
        file, formatted for open_image_file_by_path.
        """
        pathArg = filedialog.askopenfilename(title="Select Image", filetypes=(
            ("png files", ".png"), ("jpg files", ".jpg"), ("jpg files", ".jpeg")), initialdir=self.source_directory)
        split_path = pathArg.split("/")
        return split_path[len(split_path) - 1]

    def open_image_file_by_path(self, path: str):
        """
        Opens an image file and updates the canvas with it.
        Calls update_gui_with_file_data.

        Parameters
        ----------
        path: str
            the file path for the image to be loaded

        Side Effects
        ------------
            The canvas is updated
            Calls update_gui_with_file_data
        """
        # update the current file path in "state"
        self.path = path

        # open the new image
        self.image = ig.open(self.source_directory + "/" + path)
        img = ImageTk.PhotoImage(self.image)
        self.view.image_id = self.view.canvas.create_image(
            0, 0, image=img, anchor=tk.NW, tag="img")
        self.view.canvas.img = img  # Keep reference.

        # reset canvas dimensions
        self.view.canvas.configure(width=img.width(), height=img.height(
        ), scrollregion=self.view.canvas.bbox("all"))

        # update_gui_with_file_data refreshes all GUI
        self.update_gui_with_file_data(path)

    def next_file(self):
        """
        Opens the next file

        Side Effects
        ------------
            Calls open_image_file_by_path, updating the canvas and GUI
        """
        path_index = self.model.paths.index(self.path)
        self.open_image_file_by_path(
            self.model.paths[(path_index+1) % len(self.model.paths)])

    def prev_file(self):
        """
        Opens the previous file

        Side Effects
        ------------
            Calls open_image_file_by_path, updating the canvas and GUI
        """
        path_index = self.model.paths.index(self.path)
        if path_index == 0:
            self.open_image_file_by_path(
                self.model.paths[len(self.model.paths) - 1])
        else:
            self.open_image_file_by_path(self.model.paths[path_index - 1])

    def select_start(self, event: Event):
        """
        Bound to left mouse button down. 
        Part 1 of clicking-and-dragging to position a box

        Parameters
        ----------
        event: Event
            the left mouse button down event, the
            coordinates of which are to be remembered

        Side Effects
        -----------
            The values of box_x_position, mouse_down_x, box_y_position and
            mouse_down_y are changed
        """
        # TODO: include transform_offset for the offset between cursor position and rectangle corner/side
        canvas_x = self.view.canvas.canvasx(event.x)
        canvas_y = self.view.canvas.canvasy(event.y)
        self.view.box_x_position.set(canvas_x)
        self.view.mouse_down_x.set(canvas_x)
        self.view.box_y_position.set(canvas_y)
        self.view.mouse_down_y.set(canvas_y)
        if self.tool_type == ToolType.TRANSFORM:
            boxes = list(set(self.view.canvas.find_overlapping(canvas_x,canvas_y,canvas_x,canvas_y)).intersection(set(self.view.box_ids)))
            if len(boxes) > 0:
                self.view.sidepanel.selection_list.selection_clear(self.view.selection_index)
                self.view.change_active_box(self.get_data_index_from_box_id(boxes[0]))
                self.load_selection_data(self.path,self.view.selection_index)
                box = self.model.selection_item_data[self.path][self.get_data_index_from_box_id(
                boxes[0])].coords
                self.transform_offset = (canvas_x - box[0],canvas_y - box[1])
                if not(canvas_x - box[0] <= 10 or canvas_y - box[1] <= 10 or box[2] - canvas_x <= 10 or box[3] - canvas_y <= 10):
                    self.transform_move = True
                else:
                    self.remember_coords = (box[0],box[1],box[2],box[3])
                    self.transform_x0 = True if canvas_x - box[0] <= 10 else False
                    self.transform_y0 = True if canvas_y - box[1] <= 10 else False
                    self.transform_x1 = True if box[2] - canvas_x <= 10 else False
                    self.transform_y1 = True if box[3] - canvas_y <= 10 else False

    def select_move(self, event: Event):
        """
        Bound to left mouse button held down. 
        Part 2 of clicking-and-dragging to position a box.

        Parameters
        ----------
        event: Event
            the left mouse button held down event, the
            coordinates of which are used to set the
            box's bounds

        Side Effects
        -----------
            box_x_position, box_width, box_y_position and box_height are changed
        """
        canvas_x = self.view.canvas.canvasx(event.x)
        canvas_y = self.view.canvas.canvasy(event.y)
        if self.tool_type == ToolType.TRANSFORM:
            if self.transform_move == True:
                self.view.box_x_position.set(canvas_x - self.transform_offset[0])
                self.view.box_y_position.set(canvas_y - self.transform_offset[1])
            else:
                if self.transform_x0 == True:
                    self.view.box_x_position.set(min(canvas_x,self.remember_coords[2]-1))
                    self.view.box_width.set(self.remember_coords[2] - self.view.box_x_position.get())
                elif self.transform_x1 == True:
                    self.view.box_width.set(max(canvas_x-self.remember_coords[0],1))
                if self.transform_y0 == True:
                    self.view.box_y_position.set(min(canvas_y ,self.remember_coords[3]-1))
                    self.view.box_height.set(self.remember_coords[3] - self.view.box_y_position.get())
                elif self.transform_y1 == True:
                    self.view.box_height.set(max(canvas_y -self.remember_coords[1],1))
        else:
            self.view.box_x_position.set(
                min(self.view.mouse_down_x.get(), canvas_x))
            self.view.box_width.set(abs(self.view.mouse_down_x.get() -
                            canvas_x))
            self.view.box_y_position.set(
                min(self.view.mouse_down_y.get(), canvas_y))
            self.view.box_height.set(abs(self.view.mouse_down_y.get() -
                                canvas_y))
        self.view.redraw_active_box()

    def select_end(self, event: Event):
        """
        Ends the click-and-drag to set the bounds of the current selection box

        Parameters
        ----------
        event: Event
            the mouse button up event

        Side Effects
        ------------
            Updates the model's selection item data
            Calls crop_image, updating the model's selecion item data and the GUI
        """
        x0 = self.view.box_x_position.get()
        y0 = self.view.box_y_position.get()
        x1 = self.view.box_x_position.get()+self.view.box_width.get()
        y1 = self.view.box_y_position.get()+self.view.box_height.get()
        intersecting_boxes = list(set(self.view.canvas.find_overlapping(x0,y0, x1, y1)).intersection(set(self.view.box_ids)))
        if self.tool_type == ToolType.CROP:
            self.crop_intersecting_boxes((x0, y0, x1, y1), intersecting_boxes)
        elif self.tool_type == ToolType.DELETE:
            self.delete_intersecting_boxes(
                intersecting_boxes)
        elif self.tool_type == ToolType.JOIN:
            self.join_intersecting_boxes(
                intersecting_boxes)
        elif self.tool_type == ToolType.SPLIT:
            self.split_intersecting_boxes(
                x0, intersecting_boxes)
        elif self.tool_type == ToolType.ADD:
            self.add_box((x0, y0, x1, y1))
            self.run_all_ops_on_current_selection()
        elif self.tool_type == ToolType.TRANSFORM:
            self.model.selection_item_data[self.path][self.view.selection_index].coords = (
                x0, y0, x1, y1)
            self.transform_move = False
            (self.transform_x0,self.transform_y0,self.transform_x1,self.transform_y1) = (False,False,False,False)
            self.set_boxes(self.path)
            self.run_all_ops_on_current_selection()
        elif self.tool_type == ToolType.SELECT:
            if len(intersecting_boxes) > 0:
                self.view.sidepanel.selection_list.selection_clear(self.view.selection_index)
                self.view.change_active_box(self.get_data_index_from_box_id(intersecting_boxes[0]))
                self.load_selection_data(self.path,self.view.selection_index)
        self.view.canvas.tag_lower(self.view.selection_box_id,self.view.image_id)

    def update_is_inverted_data(self, varname=None, idx=None, mode=None):
        """
        Updates the value of is_inverted for the current selection box,
        toggling whether to invert the color values prior to running ocr.
        For scanning light text on a dark background.

        Parameters
        ----------
        ???

        Side Effects
        ------------
            Updates the model's selection item data
        """
        self.model.selection_item_data[self.path][self.view.selection_index].is_inverted = bool(
            self.view.sidepanel.is_inverted.get())

    def update_is_vertical_data(self, varname=None, idx=None, mode=None):
        """
        Updates the value of is_vertical for the current selection box,
        toggling whether to set the is_vertical option when running ocr.
        For scanning text that is printed vertically.

        Parameters
        ----------
        ???

        Side Effects
        ------------
            Updates the model's selection item data
        """
        self.model.selection_item_data[self.path][self.view.selection_index].is_vertical = bool(
            self.view.sidepanel.is_vertical.get())

    def run_ocr_button_clicked(self, event=None):
        """
        Calls crop_image when the run_ocr button is clicked

        Parameters
        ----------
        event: event
            the button click event
            not used

        Side Effects
        ------------
            * The translation area is updated
            * Calls crop_image, updating the model's selecion item data and the GUI
        """
        self.run_all_ops_on_current_selection()

    def run_translation_button_clicked(self, event=None):
        """
        Translates the text of the current selection box.
        Updates the translation area with the output.

        Parameters
        ----------
        event: event
            the button click event
                not used

        Side Effects
        ------------
            * The translation area is updated
            * The value of model's selection_item_data is changed
        """
        ocr_output = self.view.sidepanel.ocr_area.get("1.0", END)
        self.model.selection_item_data[self.path][self.view.selection_index].ocr_output = ocr_output
        self.update_translation(ocr_output)

    def run_all_ops_on_current_selection(self):
        """
        Gets an image cropped to the bounds of the current selection box.
        Calls run_ocr on the cropped image.
        Updates the ocr area with the result of run_ocr.
        Calls run_translation on the ocr output.
        Updates the translation area with the result of run_translation.
        Updates preview image with the cropped image.

        Parameters
        ----------
        event: event
            the button click event
                not used

        Side Effects
        ------------
            The ocr area is updated
            The translation area is updated
            The value of model's selection_item_data is changed
            The preview image is updated
        """
        img2 = self.image.crop([self.view.box_x_position.get(), self.view.box_y_position.get(
        ), self.view.box_x_position.get()+self.view.box_width.get(), self.view.box_y_position.get()+self.view.box_height.get()])
        ocr_output = run_ocr(img2, self.model.selection_item_data[self.path][self.view.selection_index].is_inverted,
                             self.model.selection_item_data[self.path][self.view.selection_index].is_vertical, self.view.sidepanel.threshold.get())
        self.update_ocr(ocr_output)
        self.update_translation(ocr_output)
        self.model.selection_item_data[self.path][self.view.selection_index].threshold = self.view.sidepanel.threshold.get(
        )
        self.update_preview_image()

    def update_translation(self, ocr_output: str):
        self.view.sidepanel.translation_area.delete("1.0", END)
        if ocr_output != '':
            translation = get_translation(ocr_output)
            self.model.selection_item_data[self.path][self.view.selection_index].translation = translation
            self.view.sidepanel.translation_area.insert(END, translation)

    def update_ocr(self, ocr_output: str):
        self.model.selection_item_data[self.path][self.view.selection_index].ocr_output = ocr_output
        self.view.sidepanel.ocr_area.delete("1.0", END)
        self.view.sidepanel.ocr_area.insert(END, ocr_output)

    def update_preview_image(self, varname=None, idx=None, mode=None):
        """
        Updates the preview image, showing what the current selection will
        look like once the current threshold is applied

        Parameters
        ----------
        ???

        Side Effects
        ------------
            The preview image is updated
        """
        img = self.image.crop([self.view.box_x_position.get(), self.view.box_y_position.get(
        ), self.view.box_x_position.get()+self.view.box_width.get(), self.view.box_y_position.get()+self.view.box_height.get()])
        img = ImageTk.PhotoImage(make_ocr_ready(
            img, self.model.selection_item_data[self.path][self.view.selection_index].is_inverted, self.view.sidepanel.threshold.get()))
        self.view.sidepanel.preview_image.create_image(
            0, 0, image=img, anchor=tk.NW, tag="img")
        self.view.sidepanel.preview_image.img = img  # Keep reference.

    def export_button_clicked(self, event=None):
        """
        Creates the output image file with translated text.
            Incomplete.

        Parameters
        ----------
        event: event
            the button click event
                not used

        Side Effects
        ------------
            An image file is created.
        """
        img = self.image.copy()
        draw = ImageDraw.Draw(img)
        for i in self.model.selection_item_data[self.path]:
            draw.rectangle([(i.coords[0], i.coords[1]),
                           (i.coords[2], i.coords[3])], fill='white', width=0)
            draw.text(((i.coords[0]+i.coords[2])/2, (i.coords[1]+i.coords[3])/2), text=self.text_wrap(i.translation,ImageFont.truetype("arial", 20),max_width=i.coords[2]-i.coords[0]),
                      font=ImageFont.truetype("arial", 20), fill='black', anchor='mm')
        img.save(self.source_directory + '/output/' +
                 self.path.replace('.png', '-output.png'))

    def toggle_display_mode_button_clicked(self, event=None):
        """
        Toggles between displaying the original or translated text.

        Parameters
        ----------
        event: event
            the button click event
                not used

        Side Effects
        ------------
            An image file is created.
        """
        if self.display_mode == "box":
            self.display_mode = "preview"
        else:
            self.display_mode = "box"
        self.set_boxes(self.path)

    def get_bounding_boxes_button_clicked(self, event=None):
        """
        TODO

        Parameters
        ----------
        event: event
            the button click event
                not used

        Side Effects
        ------------
            TODO
        """
        self.view.box_ids.clear()
        self.view.canvas.delete('selection')
        img = make_ocr_ready(self.image, False, 127)
        custom_config = r'-l jpn+eng --psm 6'
        d = pytesseract.image_to_data(
            img, output_type=Output.DICT, config=custom_config)
        n_boxes = len(d['text'])
        for i in range(n_boxes):
            # if int(float(d['conf'][i])) > 60:
            if int(d['level'][i]) == 4:
                (x, y, w, h) = (d['left'][i], d['top']
                                [i], d['width'][i], d['height'][i])
                self.model.add_row(self.path)
                self.model.selection_item_data[self.path][len(
                    self.model.selection_item_data[self.path])-1].coords = (x,y,x+w,y+h)
        self.update_gui_with_file_data(self.path)

    def crop_intersecting_boxes(self, box: tuple[float, float, float, float], intersecting_boxes: list[int]):
        for box_id in intersecting_boxes:
            x0, y0, x1, y1 = self.view.canvas.coords(box_id)
            x0 = max(x0, box[0])
            y0 = max(y0, box[1])
            x1 = min(x1, box[2])
            y1 = min(y1, box[3])
            self.model.selection_item_data[self.path][self.get_data_index_from_box_id(
            box_id)].coords = (x0, y0, x1, y1)
        self.update_gui_with_file_data(self.path)

    def join_intersecting_boxes(self, intersecting_boxes: list[int]):
        x0, y0, x1, y1 = self.get_bounding_box(intersecting_boxes)
        self.model.selection_item_data[self.path][self.get_data_index_from_box_id(
            intersecting_boxes[0])].coords = (x0, y0, x1, y1)
        for box_id in intersecting_boxes:
            if box_id != intersecting_boxes[0]:
                self.model.delete_row(
                    self.path, self.get_data_index_from_box_id(box_id))
                self.view.box_ids.remove(box_id)
        self.update_gui_with_file_data(self.path)

    def get_bounding_box(self, intersecting_boxes: list[int]):
        x0,y0,x1,y1 = self.view.canvas.coords(intersecting_boxes[0])
        for box_id in intersecting_boxes:
            box = self.view.canvas.coords(box_id)
            x0 = min(x0, box[0])
            y0 = min(y0, box[1])
            x1 = max(x1, box[2])
            y1 = max(y1, box[3])
        return (x0,y0,x1,y1)

    def get_data_index_from_box_id(self, box_id):
        return self.view.box_ids.index(box_id)

    def delete_intersecting_boxes(self, intersecting_boxes: list[int]):
        for box_id in intersecting_boxes:
            self.model.delete_row(self.path, self.get_data_index_from_box_id(box_id))
            self.view.box_ids.remove(box_id)
        self.update_gui_with_file_data(self.path)

    def split_intersecting_boxes(self, x: float, intersecting_boxes: list[int]):
        for box_id in intersecting_boxes:
            x0, y0, x1, y1 = self.view.canvas.coords(box_id)
            self.model.selection_item_data[self.path][self.get_data_index_from_box_id(
                box_id)].coords = (x0, y0, x, y1)
            self.model.add_row(self.path)
            self.add_box((x, y0, x1, y1))
        self.update_gui_with_file_data(self.path)

    def add_box(self, box: tuple[float, float, float, float]):
        self.model.add_row(self.path)
        self.model.selection_item_data[self.path][len(
            self.model.selection_item_data[self.path])-1].coords = box
        self.update_gui_with_file_data(self.path)

    def next_tool_type(self):
        if self.tool_type == ToolType.SELECT:
            self.tool_type = ToolType.ADD
        elif self.tool_type == ToolType.ADD:
            self.tool_type = ToolType.CROP
        elif self.tool_type == ToolType.CROP:
            self.tool_type = ToolType.DELETE
        elif self.tool_type == ToolType.DELETE:
            self.tool_type = ToolType.JOIN
        elif self.tool_type == ToolType.JOIN:
            self.tool_type = ToolType.SPLIT
        elif self.tool_type == ToolType.SPLIT:
            self.tool_type = ToolType.TRANSFORM
        elif self.tool_type == ToolType.TRANSFORM:
            self.tool_type = ToolType.SELECT
        self.view.sidepanel.tool_type_label.configure(text=self.tool_type.name)

    def prev_tool_type(self):
        if self.tool_type == ToolType.SELECT:
            self.tool_type = ToolType.TRANSFORM
        elif self.tool_type == ToolType.ADD:
            self.tool_type = ToolType.SELECT
        elif self.tool_type == ToolType.CROP:
            self.tool_type = ToolType.ADD
        elif self.tool_type == ToolType.DELETE:
            self.tool_type = ToolType.CROP
        elif self.tool_type == ToolType.JOIN:
            self.tool_type = ToolType.DELETE
        elif self.tool_type == ToolType.SPLIT:
            self.tool_type = ToolType.JOIN
        elif self.tool_type == ToolType.TRANSFORM:
            self.tool_type = ToolType.SPLIT
        self.view.sidepanel.tool_type_label.configure(text=self.tool_type.name)

    def set_tool_type(self, tool_type):
        self.tool_type = tool_type
        self.view.sidepanel.tool_type_label.configure(text=self.tool_type.name)
    
    def text_wrap(self, text:str, font: ImageFont, max_width):
        lines = ""
        # If the width of the text is smaller than image width
        # we don't need to split it, just add it to the lines array
        # and return
        if font.getlength(text) <= max_width:
            lines = text
        else:
            # split the line by spaces to get words
            words = text.split(' ')  
            i = 0
            # append every word to a line while its width is shorter than image width
            while i < len(words):
                line = ''         
                while i < len(words) and font.getlength(line + words[i]) <= max_width:                
                    line = line + words[i] + " "
                    i += 1
                if not line:
                    line = words[i]
                    i += 1
                # when the line gets longer than the max width do not append the word, 
                # add the line to the lines array
                lines = lines + "\n" + line if lines else line
        return lines

if __name__ == '__main__':
    c = Controller()
    c.root.mainloop()
