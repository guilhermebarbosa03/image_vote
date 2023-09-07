import tkinter as tk
from PIL import Image, ImageTk, ImageFile
from tkinter import ttk, filedialog
import pygame
import os
import math
import random
import re
import shutil

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Base program interface and functionalities
class Application:
    def __init__(self):
        # Main window settings
        self.root = tk.Tk()
        self.root.geometry("1280x720")
        self.root.config(bg="#282D2F")
        self.root.minsize(250, 200)
        self.root.state("zoomed")
        self.filepath = ""
        self.background_color = "#282D2F"
        self.button_style = {
            "background": "#515A60",
            "activebackground": "#E0E0E0",
            "foreground": "#FFFFFF",
            "bd": 0,
            "disabledforeground": "#929B91",
        }
        self.root.update()

        self.audio_button_press_exists = False
        self.audio_button_release_exists = False
        self.audio_image_grab_exists = False
        self.audio_image_release_exists = False

        self.start_screen()  # Load starting screen
        self.audio_setup()

    # Set up sound effects
    def audio_setup(self):
        pygame.mixer.init()
        if os.path.exists("./audio/big_tap.mp3"):
            self.audio_button_press_exists = True
            self.audio_button_press = pygame.mixer.Sound("./audio/big_tap.mp3")
            pygame.mixer.Sound.set_volume(self.audio_button_press, 0.5)
        if os.path.exists("./audio/big_tap_end.mp3"):
            self.audio_button_release_exists = True
            self.audio_button_release = pygame.mixer.Sound("./audio/big_tap_end.mp3")
            pygame.mixer.Sound.set_volume(self.audio_button_release, 0.7)
        if os.path.exists("./audio/short_tap.mp3"):
            self.audio_image_grab_exists = True
            self.audio_image_grab = pygame.mixer.Sound("./audio/short_tap.mp3")
            pygame.mixer.Sound.set_volume(self.audio_image_grab, 0.5)
        if os.path.exists("./audio/short_tap_low.mp3"):
            self.audio_image_release_exists = True
            self.audio_image_release = pygame.mixer.Sound("./audio/short_tap_low.mp3")
            pygame.mixer.Sound.set_volume(self.audio_image_release, 1.15)

    # Create and load widgets for the start screen
    def start_screen(self):
        # Backgrounds
        self.start_container = tk.Frame(self.root, bg=self.background_color)
        self.folder_container = tk.Frame(self.start_container, bg=self.background_color)

        # Buttons
        self.folder_button = tk.Button(
            self.folder_container,
            text="Select Folder",
            command=self.open_folder,
            font=("Helvetica", 16),
            **self.button_style,
        )
        self.start_button = tk.Button(
            self.start_container,
            text="Start",
            font=("Helvetica", 36),
            command=self.start_poll,
            state=tk.DISABLED,
            **self.button_style,
        )
        self.rename_screen_button = tk.Button(
            self.root,
            text="Rename Images",
            command=self.rename_screen,
            font=("Helvetica", 16),
            **self.button_style,
        )

        # Warnings
        self.folder_warning = tk.Label(
            self.start_container,
            text="Invalid Folder.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 12),
        )
        self.image_warning = tk.Label(
            self.start_container,
            text='The images are not set up properly.\nUse the "Rename Images" button at the bottom!',
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 12),
        )
        self.file_warning = tk.Label(
            self.start_container,
            text="The files in the folder are not valid images.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 12),
        )

        # Text
        self.title = tk.Label(
            self.root,
            background=self.background_color,
            fg="white",
            font=("Helvetica", 48, "bold"),
            text="Image Vote",
        )
        self.path_label = tk.Label(
            self.folder_container,
            bg=self.background_color,
            fg="white",
            font=("Helvetica", 12),
        )
        self.rename_label = tk.Label(
            self.root,
            text="You have to click here to set up the images!",
            bg=self.background_color,
            fg="white",
            font=("Helvetica", 12),
        )
        self.loading_label = tk.Label(
            self.root,
            text="Loading...",
            bg=self.background_color,
            fg="white",
            font=("Helvetica", 32, "bold"),
        )

        # Load widgets
        self.load_start()

    # Load the starting screen
    def load_start(self):
        self.title.pack(pady=100)
        self.start_container.place(relx=0.5, rely=0.4, anchor="n", width=1024)
        self.folder_container.pack(anchor="center", pady=(0, 5), fill="x", expand=True)
        self.folder_button.grid(row=0, column=1)
        self.path_label.grid(row=0, column=0, sticky="e")
        self.folder_container.grid_columnconfigure(0, weight=1, minsize=437)
        self.folder_container.grid_columnconfigure(1, weight=1, minsize=150)
        self.folder_container.grid_columnconfigure(2, weight=1, minsize=437)
        self.start_button.pack(anchor="center")
        self.rename_screen_button.pack(side=tk.BOTTOM, pady=(5, 10))
        self.rename_label.pack(side=tk.BOTTOM)

        self.start_button.bind("<ButtonPress-1>", self.play_button_press)
        self.folder_button.bind("<ButtonPress-1>", self.play_button_press)
        self.folder_button.bind("<ButtonRelease-1>", self.play_button_release)
        self.rename_screen_button.bind("<ButtonPress-1>", self.play_button_press)
        self.rename_screen_button.bind("<ButtonRelease-1>", self.play_button_release)

    # Count variants and check if they are consistent for every level
    def count_variants(self):
        variants_dict = {}

        for filename in os.listdir(self.filepath):
            basename = re.sub(r"\d*\.\w+$", r"", filename)
            # Add 1 to the count of levels of the variant
            variants_dict[basename] = variants_dict.get(basename, 0) + 1
        variant_values = list(variants_dict.values())

        if len(set(variant_values)) != 1:
            return False
        else:
            return len(variants_dict.keys())

    # Calculate aspect ratio of the images based on the first one, the rest will be stretched to the same aspect ratio if different
    def calculate_aspect(self):
        with Image.open(
            os.path.normpath(os.path.join(self.filepath, self.imagelist[0]))
        ) as img:
            self.base_resolution = img.size
            gcd = math.gcd(self.base_resolution[0], self.base_resolution[1])
            self.aspectratio = (
                self.base_resolution[0] / gcd,
                self.base_resolution[1] / gcd,
            )

    # Get the selected folder, removes previous warnings and enable Start Button
    def open_folder(self):
        self.filepath = filedialog.askdirectory()
        self.path_label.config(text=f"Folder: {self.filepath}")
        if self.filepath:
            # Remove warnings
            self.folder_warning.pack_forget()
            self.image_warning.pack_forget()
            self.file_warning.pack_forget()

            # Enable Start Button
            self.start_button.config(state=tk.NORMAL)

    # Load and start the polls
    def start_poll(self):
        self.play_button_release()
        try:
            self.imagelist = os.listdir(self.filepath)
        except Exception as e:
            # Show warning if there is an error
            self.folder_warning.config(text=f"Error {e}")
            self.folder_warning.pack()
            return

        # Check if all the files are valid images
        for file in self.imagelist:
            try:
                with Image.open(
                    os.path.normpath(os.path.join(self.filepath, file))
                ) as img:
                    pass
            except:
                self.file_warning.pack()
                return

        self.titledict = {}  # Dictionary with the number identifier of the variant and its name
        self.pages = []  # List with objects for each level's page
        self.results = [] # List of lists with the resulting order of image variants for each page


        self.calculate_aspect()
        self.total_variants_count = self.count_variants()

        # Show warning if inconsistent number of variants for the pages
        if not self.total_variants_count:
            self.image_warning.pack()
            return
        
        # Clear current screen
        self.title.pack_forget()
        self.start_container.place_forget()
        self.rename_screen_button.pack_forget()
        self.rename_label.pack_forget()
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

        self.templist = []  # List used to create self.separated_images list
        self.separated_images = []  # List of lists of images for each page
        self.level_index = 0  # Counter for the level when creating self.separated_images list
        self.current_page = 0  # Number of the current page
        self.variant_index = 0 # Counter for the variants in the loop
        self.imagecount = len(self.imagelist)
        self.levelsize = int(self.imagecount/self.total_variants_count)

        # Add the images to the separated_list
        for counter in range(self.imagecount):
            if counter < self.total_variants_count:
                self.titledict[self.variant_index] = re.sub(r"\d*\.\w+$", r"", self.imagelist[self.levelsize*self.variant_index])

            self.templist.append(self.imagelist[self.level_index + self.levelsize*self.variant_index])
            self.variant_index += 1
            # Add to self.separated_images if at the last image of the variation
            if (self.variant_index) % (self.total_variants_count) == 0:
                self.separated_images.append(self.templist)
                self.templist = []
                self.level_index += 1
                self.variant_index = 0

        # Create dictionary with the number id of the variants and their current score
        self.pointdict = {i: 0 for i in range(self.total_variants_count)}
        # Load the page levels
        for count, page in enumerate(self.separated_images):
            self.pages.append(Level(self, page))
            self.pages[count].canvas.pack_forget()

        self.last_page_index = len(self.pages) - 1

        self.next_button = tk.Button(
            self.root,
            text="Next",
            font=("Helvetica", 24),
            borderwidth=0,
            fg="#FFFFFF",
            disabledforeground="#888888",
            command=self.show_next_page,
            activebackground="#D0D0D0",
        )
        self.next_button.pack(side="right", fill="y")
        self.loading_label.place_forget()
        self.show_page(0)  # Show the first level

        self.next_button.bind(
            "<ButtonPress-1>", self.play_button_press
        )  # Bind sound to the "Next" button

    # Play audio when pressing button
    def play_button_press(self, event=None):
        if self.audio_button_press_exists:
            self.audio_button_press.play()

    # Play audio when releasing button
    def play_button_release(self, event=None):
        if self.audio_button_release_exists:
            self.audio_button_release.play()

    def play_image_grab(self):
        if self.audio_image_grab_exists:
            self.audio_image_grab.play()

    def play_image_release(self):
        if self.audio_image_release_exists:
            self.audio_image_release.play()

    # Hide current page and show the next one
    def show_page(self, page_number):
        self.pages[self.current_page].canvas.pack_forget()  # Hide current page
        self.current_page = page_number  # Update page index
        self.pages[self.current_page].canvas.pack(anchor="nw", side=tk.LEFT, fill="both", expand=True)  # Load next page
        # Update next page data
        self.pages[self.current_page].canvas.update()
        self.pages[self.current_page].adjust_sizes()
        self.update_button()
        self.root.config(bg=self.pages[self.current_page].color)

    # Update the 'Next' button
    def update_button(self):
        self.next_button.config(bg=self.pages[self.current_page].color)  # Change color to fit the current page
        self.next_button.config(state=tk.DISABLED)  # Disable button
        if self.current_page == self.last_page_index:
            self.next_button.config(command=lambda: self.finish_game())  # Load final screen if in the last page

    # Save current page results and run show_page
    def show_next_page(self):
        self.play_button_release()
        self.results.append(self.pages[self.current_page].slotted_image_list)  # Save current page results
        if self.current_page < self.last_page_index:
            self.show_page(self.current_page + 1)

    # Enable button if all slots are filled
    def button_check(self):
        if not 0 in self.pages[self.current_page].slotted_image_list:
            self.next_button.config(state=tk.NORMAL)
        else:
            self.next_button.config(state=tk.DISABLED)

    # Calculate ranking results and show final screen
    def finish_game(self):
        self.play_button_release()

        # Save last page results
        self.results.append(self.pages[self.current_page].slotted_image_list)
        # Switch next button for a finish button
        self.next_button.pack_forget()
        self.end_button = tk.Button(
            self.root,
            text="Finish",
            font=("Helvetica", 24),
            borderwidth=0,
            width=6,
            bg="#515A60",
            fg="#FFFFFF",
            command=lambda: self.root.destroy(),
            activebackground="#D0D0D0",
        )
        self.end_button.pack(side=tk.RIGHT, fill="y")

        # Bind audio to the last button
        self.end_button.bind("<ButtonPress-1>", self.play_button_press)
        self.end_button.bind("<ButtonRelease-1>", self.play_button_release)

        self.calculate_score()
        self.ranking_screen()

    # Calculate the score of each variant
    def calculate_score(self):
        for pageresult in self.results:
            for subtractor, identifier in enumerate(pageresult):
                self.pointdict[identifier - 2 - math.ceil(self.total_variants_count / 2)] += (self.total_variants_count - 1 - subtractor)
        self.finaldict = {
            self.titledict[key[0]]: self.pointdict[key[0]]
            for key in sorted(self.pointdict.items(), key=lambda item: -item[1])
        }

    # Adjust size of the scroll region of the ranking list when resizing window
    def ranking_configure(self, event):
        self.rankingcanvas.itemconfig(1, width=self.rankingcanvas.winfo_width())
        if self.canvasgrid.bbox("all")[3] > self.rankingcanvas.winfo_height():
            self.rankingcanvas.configure(
                scrollregion=(
                    0,
                    0,
                    self.canvasgrid.bbox("all")[2],
                    self.canvasgrid.bbox("all")[3],
                )
            )
        else:
            self.rankingcanvas.configure(
                scrollregion=(
                    0,
                    0,
                    self.canvasgrid.bbox("all")[2],
                    self.rankingcanvas.winfo_height(),
                )
            )

    # Load the screen with the ranking
    def ranking_screen(self):
        # Change background color and clear current screen
        self.root.config(bg="#282D2F")
        self.pages[self.current_page].canvas.pack_forget()

        self.contestantnamelist = []
        self.contestantpointlist = []
        self.separator = []
        self.horizontalseparatorlist = []

        # Creating the widgets
        self.rankingframe = tk.Frame(self.root)
        self.rankingcanvas = tk.Canvas(self.rankingframe, bg="#383D3F", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(
            self.rankingframe,
            orient="vertical",
            command=self.rankingcanvas.yview(),
            bg="#50565B",
            troughcolor="#383D3F",
        )
        self.canvasgrid = tk.Frame(self.rankingcanvas, bg="#50565B")

        # Load the widgets
        self.rankingframe.pack(
            anchor=tk.CENTER, fill=tk.BOTH, expand=True, padx=250, pady=50
        )
        self.rankingcanvas.pack(side=tk.LEFT, expand=True, fill="both", padx=0)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.rankingcanvas.config(yscrollcommand=self.scrollbar.set)
        self.rankingcanvas.update()
        self.rankingcanvas.create_window(
            4,
            4,
            window=self.canvasgrid,
            anchor="nw",
            width=self.rankingcanvas.winfo_width() - 8,
        )
        # Load variant names and scores
        contestant_index = 0
        for contestant, point in self.finaldict.items():
            self.canvasgrid.columnconfigure(0, weight=1)
            self.separator.append(ttk.Separator(self.canvasgrid, orient="horizontal"))
            self.horizontalseparatorlist.append(tk.Frame(self.canvasgrid, bg="#50565B"))
            self.contestantnamelist.append(
                tk.Label(
                    self.horizontalseparatorlist[contestant_index],
                    text=contestant,
                    font=("Helvetica", 24),
                    background="#50565B",
                    foreground="#E0E0E0",
                )
            )
            self.contestantpointlist.append(
                tk.Label(
                    self.horizontalseparatorlist[contestant_index],
                    text=(f"Score: {point}"),
                    font=("Helvetica", 24),
                    background="#50565B",
                    foreground="#E0E0E0",
                )
            )
            self.horizontalseparatorlist[contestant_index].grid(
                row=contestant_index * 2, sticky="we"
            )
            self.contestantnamelist[contestant_index].pack(padx=10, side=tk.LEFT)
            self.contestantpointlist[contestant_index].pack(side=tk.RIGHT, padx=10)
            self.separator[contestant_index].grid(
                row=(contestant_index * 2 + 1), column=0, sticky="we"
            )
            self.canvasgrid.rowconfigure(contestant_index * 2, weight=1, minsize=75)
            contestant_index += 1

        self.rankingcanvas.bind_all(
            "<MouseWheel>",
            lambda e: self.rankingcanvas.yview_scroll(
                int(-1 * (e.delta / 60)), "units"
            ),
        )

        self.separator[-1].destroy()

        # Adjust scroll region size
        if self.canvasgrid.bbox("all")[3] > self.rankingcanvas.winfo_height():
            self.rankingcanvas.configure(
                scrollregion=(
                    0,
                    0,
                    self.canvasgrid.bbox("all")[2],
                    self.canvasgrid.bbox("all")[3],
                )
            )
        else:
            self.rankingcanvas.configure(
                scrollregion=(
                    0,
                    0,
                    self.canvasgrid.bbox("all")[2],
                    self.rankingcanvas.winfo_height(),
                )
            )

        self.rankingcanvas.bind("<Configure>", self.ranking_configure)

    # Close the app when finished
    def close_app(self):
        self.root.destroy()

    # ----------------------------------------------------------------------File Renamer---------------------------------------------------------------------------- #

    # Use this to rename the images based on their variants so they can be used in the poll. A variant can be any type of variation, like a different camera, different weather, perspective, etc.
    # They will be renamed in batches for each stage/level, with the variant as the title and the stage identified by the number at the end (e.g., "FirstVariant1","FirstVariant2","SecondVariant1","SecondVariant2")
    # All levels need the same number of variants

    # The page for renaming the images
    def rename_screen(self):
        self.variant_entries = []
        self.variant_labels = []
        self.variant_files_button = []
        self.variant_add_file_button = []
        self.variant_remove_file_button = []
        self.variant_path_labels = []
        self.rename_filepath = [[]]
        self.variant_count = 1

        # Clear main screen
        self.title.pack_forget()
        self.start_container.place_forget()
        self.rename_screen_button.pack_forget()
        self.rename_label.pack_forget()

        # Create containers for the widgets
        self.rename_container = tk.Frame(self.root, bg=self.background_color)
        self.variant_container = tk.Frame(self.rename_container, bg="#74868f")
        self.variant_labels_container = tk.Frame(
            self.rename_container, bg=self.background_color
        )
        self.modify_variant_container = tk.Frame(self.variant_container, bg="#74868f")
        self.variant_paths_container = tk.Frame(
            self.rename_container, bg=self.background_color
        )

        # List with text entries for the variant names
        self.variant_entries.append(
            tk.Entry(
                self.variant_container,
                font=("Helvetica", 11),
                bg=self.button_style["background"],
                foreground="white",
                bd=0,
                insertbackground="white",
            )
        )
        self.variant_labels.append(
            tk.Label(
                self.variant_labels_container,
                font=("Helvetica", 11),
                bg=self.background_color,
                foreground="white",
                text="Variant 1",
            )
        )

        # Texts
        self.rename_title = tk.Label(
            self.root,
            background=self.background_color,
            fg="white",
            font=("Helvetica", 48, "bold"),
            text="Rename Images",
        )
        self.rename_disclaimer = tk.Label(
            self.root,
            background=self.background_color,
            fg="white",
            font=("Helvetica", 11),
            text="1) Use this to create a folder with the renamed images based on their variants, so they can be used in the poll. A variant can be any type of variation, like a different camera, different weather, perspective, etc.\n\n2) The files will be renamed with the variant as the title and the stage identified by the number at the end (e.g., 'FirstVariant1' and 'SecondVariant1' for the first level,'FirstVariant2' and 'SecondVariant2' for the second level).\n\n3) If you use the 'Files' button, you can select multiple images at once, but they their stages will be defined by their names in alphabetical order. If the files are not sorted alphabetically, use the 'Add 1' button to add the files one-by-one in order.\n\n4) All levels need the same number of variants. A new folder called 'renamed_files' in the current directory will be created.",
        )
        self.variant_path_labels.append(
            tk.Label(
                self.variant_paths_container,
                bg=self.background_color,
                fg="white",
                font=("Helvetica", 10),
            )
        )

        # Warnings
        self.rename_warning = tk.Label(
            self.root,
            text="File not found.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 11),
        )
        self.empty_entry_warning = tk.Label(
            self.root,
            text="Can't have empty variant name.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 11),
        )
        self.variant_number_incompatible_warning = tk.Label(
            self.root,
            text="Number of files needs to be a multiple of the number of variants and all variants need the same number of images.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 11),
        )
        self.successful_rename_warning = tk.Label(
            self.root,
            text="Files renamed successfully.",
            bg=self.background_color,
            fg="white",
            font=("Helvetica", 11),
        )
        self.error_rename_warning = tk.Label(
            self.root,
            text="Error renaming files.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 11),
        )
        self.repeated_variant_warning = tk.Label(
            self.root,
            text="Can't have repeated variant names.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 11),
        )
        self.no_special_warning = tk.Label(
            self.root,
            text="Variant names can only be letters.",
            bg=self.background_color,
            fg="red",
            font=("Helvetica", 11),
        )

        # Buttons
        self.rename_button = tk.Button(
            self.rename_container,
            text="Rename",
            font=("Helvetica", 24),
            **self.button_style,
            state=tk.DISABLED,
            command=self.setup_renaming,
        )
        self.back_button = tk.Button(
            self.root,
            **self.button_style,
            font=("Helvetica", 20),
            text="Back",
            command=self.go_back_screen,
        )
        self.variant_add_button = tk.Button(
            self.modify_variant_container,
            text="Add",
            font=("Helvetica", 10),
            **self.button_style,
            command=self.increase_variant,
        )
        self.variant_remove_button = tk.Button(
            self.modify_variant_container,
            text="Remove",
            font=("Helvetica", 10),
            **self.button_style,
            command=self.decrease_variant,
        )
        self.variant_files_button.append(
            tk.Button(
                self.variant_container,
                text="Files",
                **self.button_style,
                command=lambda: self.open_folder_rename(0, True),
            )
        )
        self.variant_add_file_button.append(
            tk.Button(
                self.variant_container,
                text="Add 1",
                **self.button_style,
                command=lambda: self.open_folder_rename(0),
            )
        )
        self.variant_remove_file_button.append(
            tk.Button(
                self.variant_container,
                text="Remove",
                **self.button_style,
                command=self.remove_file_rename,
            )
        )

        # Load the widgets
        self.rename_title.pack(pady=(100, 0))
        self.rename_disclaimer.pack(pady=5)
        self.rename_container.pack(pady=(50, 5))
        self.rename_button.grid(row=3, column=1, pady=(40))
        self.back_button.pack(side=tk.BOTTOM, pady=(5, 10))
        self.rename_container.grid_columnconfigure(0, weight=1, minsize=437)
        self.rename_container.grid_columnconfigure(1, weight=1, minsize=150)
        self.rename_container.grid_columnconfigure(2, weight=1, minsize=437)
        self.variant_container.grid(row=5, column=1)
        self.variant_labels_container.grid(row=5, column=0, sticky="ne")
        self.variant_paths_container.grid(row=5, column=2, sticky="nw")
        self.variant_entries[0].grid(row=0, column=0, pady=2, padx=(2, 0))
        self.variant_files_button[0].grid(row=0, column=1, padx=2)
        self.variant_add_file_button[0].grid(row=0, column=2, padx=2)
        self.variant_files_button[0].grid(row=0, column=1, padx=2)
        self.variant_labels[0].grid(row=0, column=0, sticky="ne")
        self.variant_path_labels[0].grid(row=0, column=0, sticky="nw")
        self.modify_variant_container.grid(row=1, column=0)
        self.variant_add_button.grid(row=0, column=0, pady=2)

        # Bind the sounds for the buttons
        self.rename_button.bind("<ButtonPress-1>", self.play_button_press)
        self.variant_add_button.bind("<ButtonPress-1>", self.play_button_press)
        self.variant_files_button[0].bind("<ButtonPress-1>", self.play_button_press)
        self.variant_add_file_button[0].bind("<ButtonPress-1>", self.play_button_press)
        self.variant_add_button.bind("<ButtonPress-1>", self.play_button_press)
        self.variant_remove_button.bind("<ButtonPress-1>", self.play_button_press)
        self.back_button.bind("<ButtonPress-1>", self.play_button_press)
        self.rename_button.bind("<ButtonRelease-1>", self.play_button_release)
        self.back_button.bind("<ButtonRelease-1>", self.play_button_release)
        self.variant_add_button.bind("<ButtonRelease-1>", self.play_button_release)
        self.variant_remove_button.bind("<ButtonRelease-1>", self.play_button_release)

    # Get the folder of the files to be renamed
    def open_folder_rename(self, index=0, multiple=False):
        if multiple:
            self.rename_filepath[index] = list(
                filedialog.askopenfilenames(
                    title="Select Images",
                    filetypes=(
                        ("Image files", "*.png *.jpeg *.jpg *.gif *.bmp *.tiff"),
                        ("All files", "*.*"),
                    ),
                )
            )
        else:
            new_file = filedialog.askopenfilename(
                title="Select Images",
                filetypes=(
                    ("Image files", "*.png *.jpeg *.jpg *.gif *.bmp *.tiff"),
                    ("All files", "*.*"),
                ),
            )
            if new_file:
                self.rename_filepath[index].append(new_file)

        current_variant_length = len(self.rename_filepath[index])
        if self.rename_filepath[index]:
            self.variant_path_labels[index].config(
                text=f"{current_variant_length} image(s) selected"
            )
            self.check_variants()
        if current_variant_length > 0:
            self.variant_remove_file_button[index].grid(row=index, column=3, padx=2)
            self.variant_remove_file_button[index].bind(
                "<ButtonPress-1>", self.play_button_press
            )
            self.variant_remove_file_button[index].bind(
                "<ButtonRelease-1>", self.play_button_release
            )
        else:
            self.variant_remove_file_button[index].grid_forget()

    def remove_file_rename(self, index=0):
        del self.rename_filepath[index][-1]
        current_variant_length = len(self.rename_filepath[index])
        self.variant_path_labels[index].config(
            text=f"{current_variant_length} image(s) selected"
        )
        self.check_variants()
        if current_variant_length == 0:
            self.variant_remove_file_button[index].grid_forget()

    # Check if variants have the same number of files
    def check_variants(self):
        self.successful_rename_warning.pack_forget()
        self.variant_number_incompatible_warning.pack_forget()
        # Check if first variant is not empty
        if len(self.rename_filepath[0]) == 0:
            return
        last_len = len(self.rename_filepath[0])
        # Check if variants have same amount of images
        for path in self.rename_filepath[1:]:
            if not path:
                self.rename_button.config(state=tk.DISABLED)
                return
            if len(path) != last_len:
                self.variant_number_incompatible_warning.pack()
                self.rename_button.config(state=tk.DISABLED)
                return
            last_len = len(path)
        self.rename_button.config(state=tk.NORMAL)

    # Increase the number of variants by 1
    def increase_variant(self):
        self.variant_count += 1
        self.rename_filepath.append([])
        self.rename_button.config(state=tk.DISABLED)

        # Create widgets
        self.variant_entries.append(
            tk.Entry(
                self.variant_container,
                font=("Helvetica", 11),
                bg=self.button_style["background"],
                foreground="white",
                bd=0,
                insertbackground="white",
            )
        )
        self.variant_labels.append(
            tk.Label(
                self.variant_labels_container,
                font=("Helvetica", 11),
                bg=self.background_color,
                foreground="white",
                text=f"Variant {self.variant_count}",
            )
        )
        self.variant_files_button.append(
            tk.Button(
                self.variant_container,
                text="Files",
                **self.button_style,
                command=lambda i=self.variant_count: self.open_folder_rename(
                    i - 1, True
                ),
            )
        )
        self.variant_path_labels.append(
            tk.Label(
                self.variant_paths_container,
                bg=self.background_color,
                fg="white",
                font=("Helvetica", 10),
            )
        )

        self.variant_add_file_button.append(
            tk.Button(
                self.variant_container,
                text="Add 1",
                **self.button_style,
                command=lambda i=self.variant_count: self.open_folder_rename(i - 1),
            )
        )
        self.variant_remove_file_button.append(
            tk.Button(
                self.variant_container,
                text="Remove",
                **self.button_style,
                command=lambda i=self.variant_count: self.remove_file_rename(i - 1),
            )
        )
        # Load widgets
        self.variant_entries[-1].grid(
            row=self.variant_count - 1, column=0, pady=2, padx=(2, 0)
        )
        self.variant_labels[-1].grid(row=self.variant_count - 1, column=0)
        self.variant_path_labels[-1].grid(row=self.variant_count - 1, column=0)
        self.variant_files_button[-1].grid(row=self.variant_count - 1, column=1)
        self.variant_add_file_button[-1].grid(row=self.variant_count - 1, column=2)
        self.modify_variant_container.grid_configure(row=self.variant_count)

        if self.variant_count == 2:
            self.variant_remove_button.grid(row=0, column=1, padx=(2, 0), pady=2)

        self.variant_files_button[self.variant_count - 1].bind(
            "<ButtonPress-1>", self.play_button_press
        )
        self.variant_add_file_button[self.variant_count - 1].bind(
            "<ButtonPress-1>", self.play_button_press
        )

    # Decrease the number of variants by 1
    def decrease_variant(self):
        # Remove widgets
        self.variant_count -= 1
        
        del self.rename_filepath[-1]
        self.variant_path_labels[-1].grid_forget()
        del self.variant_path_labels[-1]
        self.variant_entries[-1].grid_forget()
        del self.variant_entries[-1]
        self.variant_labels[-1].grid_forget()
        del self.variant_labels[-1]
        self.variant_files_button[-1].grid_forget()
        del self.variant_files_button[-1]
        self.variant_add_file_button[-1].grid_forget()
        del self.variant_add_file_button[-1]
        self.variant_remove_file_button[self.variant_count].grid_forget()
        del self.variant_remove_file_button[self.variant_count]

        self.modify_variant_container.grid_configure(row=self.variant_count)
        if self.variant_count == 1:
            self.variant_remove_button.grid_forget()
        self.check_variants()

    # Check if folder, variant count and names are OK and run the rename function
    def setup_renaming(self):
        # Clear main screen
        self.error_rename_warning.pack_forget()
        self.successful_rename_warning.pack_forget()
        self.rename_warning.pack_forget()
        self.empty_entry_warning.pack_forget()
        self.repeated_variant_warning.pack_forget()
        self.no_special_warning.pack_forget()
        self.variant_number_incompatible_warning.pack_forget()

        # If valid, check if variant names are not empty
        self.variant_names = [""] * len(self.variant_entries)
        for i, entry in enumerate(self.variant_entries):
            self.variant_names[i] = entry.get()
            if self.variant_names[i] == "":
                self.empty_entry_warning.pack()
                return
            elif not self.variant_names[i].isalpha():
                self.no_special_warning.pack()
                return
        if len(self.variant_names) != len(set(self.variant_names)):
            self.repeated_variant_warning.pack()
            return

        # Run function to create the renamed files on a new folder
        try:
            self.rename()
            self.successful_rename_warning.pack()

        # Show a warning if there is an error
        except Exception as e:
            self.error_rename_warning.config(text=f"Error {e}")
            self.error_rename_warning.pack()

    # Add renamed files to output folder
    def rename(self):
        output_path = os.path.normpath(
            os.path.join(os.path.abspath(os.curdir), "renamed_files")
        )
        if os.path.exists(output_path) and os.path.isdir(output_path):
            shutil.rmtree(output_path)
        os.mkdir(output_path)
        for variant_number, variant_files in enumerate(self.rename_filepath):
            for stage, file in enumerate(variant_files):
                new_filename = (
                    f"{self.variant_names[variant_number]}{stage+1}"
                    + os.path.splitext(file)[1]
                )  # Generate the new name of the file: Variant + Stage_counter
                shutil.copy(
                    file,
                    os.path.normpath(
                        os.path.join(output_path, os.path.basename(new_filename))
                    ),
                )  # Copy image to output folder with new name

    # Go from the renaming screen to the starting screen
    def go_back_screen(self):
        # Clear renaming screen
        self.error_rename_warning.pack_forget()
        self.rename_title.pack_forget()
        self.rename_disclaimer.pack_forget()
        self.rename_container.pack_forget()
        self.back_button.pack_forget()
        self.rename_warning.pack_forget()
        self.empty_entry_warning.pack_forget()
        self.repeated_variant_warning.pack_forget()
        self.no_special_warning.pack_forget()
        self.successful_rename_warning.pack_forget()
        self.variant_number_incompatible_warning.pack_forget()

        # Load starting screen
        self.load_start()

    # ------------------------------------------------------------------------------------------------------------------------------------------------------------------ #


# Class for the pages of the levels
class Level:
    def __init__(self, app_object, page_images):
        self.slotted_image_list = [
            0
        ] * app_object.total_variants_count  # List with all slots and the image they contain
        self.photos_list = (
            []
        )  # List of ImageTk.PhotoImage objects of the resized images
        self.photos_list_resized = []  # List of ImageTk.PhotoImage objects
        self.images_list_original = []  # List of the images with their original size
        self.images_list_resized = (
            []
        )  # List of the images after resizing to fit in the slots
        self.image_objects_list = []  # List with all objects of each image of the page
        self.spawnpoint_list = [
            (0, 0)
        ]  # List of generated spawn coordinates for each image of the page
        self.app_object = app_object  # Application class object
        self.page_images = page_images  # List with the images of the current page

        # Creating and loading page widgets
        self.canvas = tk.Canvas(
            self.app_object.root, bg="#282D2F", highlightthickness=0
        )
        self.canvas.pack(anchor="nw", side=tk.LEFT, padx=(0, 50), fill="both")
        self.app_object.start_container.lift()
        self.canvas.update()
        self.slot_background = self.canvas.create_rectangle(0, 0, 1, 1)
        self.slot_border = [
            self.canvas.create_rectangle(0, 0, 1, 1)
            for _ in range(math.ceil(self.app_object.total_variants_count / 2))
        ]

        self.calculate_size()
        self.spawn_images()

        self.canvas.itemconfig(self.slot_background, fill=self.color)
        self.tooltip = tk.Label(
            self.canvas,
            background=self.bright_color,
            foreground="#FFFFFF",
            text="Drag images with left-click\nRight-click on images to zoom in\nThe higher the image, the higher the score",
            font=("Helvetica", 10, "bold"),
        )
        self.tooltip.place(x=20, y=20)
        self.canvas.update()
        self.canvas.focus_set()
        self.canvas.bind("<Configure>", lambda e: self.calculate_size(e, True))

    # Load the image files into image objects and get color for the background
    def spawn_images(self):
        for x, imagefile in enumerate(self.page_images):
            self.random_spawn_points()
            self.images_list_original.append(
                Image.open(
                    os.path.normpath(os.path.join(self.app_object.filepath, imagefile))
                )
            )
            self.images_list_resized.append(
                self.images_list_original[x].resize(
                    (self.image_resolution[0], self.image_resolution[1])
                )
            )
            self.photos_list.append(ImageTk.PhotoImage(self.images_list_resized[x]))
            self.image_objects_list.append(
                ImageClass(
                    self.canvas,
                    self.photos_list,
                    x,
                    self.spawnpoint_list[x + 1],
                    self,
                    self.app_object,
                )
            )

        # Get the average color of one of the page's images to set as background
        self.colorgetter = self.images_list_resized[0].resize((1, 1))
        self.avg_color = self.colorgetter.getpixel((0, 0))
        self.color = f"#{int(self.avg_color[0]*0.75):02x}{int(self.avg_color[1]*0.75):02x}{int(self.avg_color[2]*0.75):02x}"
        self.bright_color = (
            f"#{self.avg_color[0]:02x}{self.avg_color[1]:02x}{self.avg_color[2]:02x}"
        )
        self.canvas.config(bg=self.bright_color)

    # Calculate the maximum size available for the images at the current window size
    def calculate_size(self, event=None, re_size=False):
        resvertical = min(
            self.canvas.winfo_height() / self.app_object.total_variants_count,
            self.app_object.base_resolution[1],
        )
        reshorizontal = min(
            self.canvas.winfo_width(), self.app_object.base_resolution[0]
        )
        bottleneck = min(
            resvertical * self.app_object.aspectratio[0],
            reshorizontal * self.app_object.aspectratio[1],
        )
        self.image_resolution = (
            math.floor((bottleneck / self.app_object.aspectratio[1])),
            math.floor(bottleneck / self.app_object.aspectratio[0]),
        )
        self.adjust_sizes()
        if re_size:
            self.re_size()

    # Change info about the coordinates of the slots and resolutions
    def adjust_sizes(self):
        self.slot_centers_list = [
            (
                float((self.canvas.winfo_width()) / 2),
                self.image_resolution[1] * x + self.image_resolution[1] / 2,
            )
            for x in range(self.app_object.total_variants_count)
        ]
        for i, slot in enumerate(self.slot_border):
            self.canvas.coords(
                slot,
                (self.canvas.winfo_width() - self.image_resolution[0]) / 2,
                0 + i * 2 * self.image_resolution[1],
                (self.canvas.winfo_width() + self.image_resolution[0]) / 2,
                self.image_resolution[1] + i * 2 * self.image_resolution[1],
            )
        self.canvas.coords(
            self.slot_background,
            (self.canvas.winfo_width() - self.image_resolution[0]) / 2,
            0,
            (self.canvas.winfo_width() + self.image_resolution[0]) / 2,
            self.app_object.root.winfo_height(),
        )

        # Update info about the resolutions, sizes, slots coordinates after resizing
        fullvertical = self.canvas.winfo_height()
        fullhorizontal = self.canvas.winfo_width()
        bottleneck = min(
            fullvertical * self.app_object.aspectratio[0],
            fullhorizontal * self.app_object.aspectratio[1],
        )
        self.full_image_resolution = (
            math.floor((bottleneck / self.app_object.aspectratio[1])),
            math.floor(bottleneck / self.app_object.aspectratio[0]),
        )

        for i, image in enumerate(self.image_objects_list):
            if image.image_id in self.slotted_image_list:
                self.canvas.coords(
                    image.image_id,
                    self.slot_centers_list[
                        self.slotted_image_list.index(image.image_id)
                    ][0],
                    self.slot_centers_list[
                        self.slotted_image_list.index(image.image_id)
                    ][1],
                )
            image.outofbounds()

    # Change size of the images
    def re_size(self):
        self.photos_list_resized.clear()
        # If the new image size hasn't been loaded yet, it will use the original size as the base to not lose sharpness, but this is laggier
        if self.image_resolution[0] > self.images_list_resized[0].size[0]:
            for i, img in enumerate(self.images_list_resized):
                self.images_list_resized[i] = self.images_list_original[i].resize(
                    (self.image_resolution[0], self.image_resolution[1])
                )
                self.photos_list_resized.append(
                    ImageTk.PhotoImage(self.images_list_resized[i])
                )
                self.image_objects_list[i].photo = self.photos_list_resized[i]
                self.canvas.itemconfig(
                    self.image_objects_list[i].image_id,
                    image=self.photos_list_resized[i],
                )
        # Uses resized images as the base for the resizing (less lag)
        else:
            for i, img in enumerate(self.images_list_resized):
                img = img.resize((self.image_resolution[0], self.image_resolution[1]))
                self.photos_list_resized.append(ImageTk.PhotoImage(img))
                self.image_objects_list[i].photo = self.photos_list_resized[i]
                self.canvas.itemconfig(
                    self.image_objects_list[i].image_id,
                    image=self.photos_list_resized[i],
                )

    # Calculate the spawn coordinates randomly for one image
    def random_spawn_points(self):
        # Define if image will be on left or right side
        while True:
            if random.randint(0, 1) % 2 == 0:
                self.spawn_point_x = random.randint(
                    int(self.image_resolution[0] * 2 + self.image_resolution[0]),
                    int(self.image_resolution[0] * 4 - self.image_resolution[0] / 2),
                )
            else:
                self.spawn_point_x = random.randint(
                    int(self.image_resolution[0] / 2),
                    int(self.image_resolution[0] * 2 - self.image_resolution[0]),
                )

            self.spawn_point_y = random.randint(
                int(self.image_resolution[1] / 2),
                int(
                    self.image_resolution[1] * self.app_object.total_variants_count
                    - self.image_resolution[1] / 2
                ),
            )

            # Check if images are far enough apart for each other
            self.distances = [
                math.dist((self.spawn_point_x, self.spawn_point_y), p)
                for p in self.spawnpoint_list
            ]
            if min(self.distances) > self.image_resolution[1]:
                self.spawnpoint_list.append((self.spawn_point_x, self.spawn_point_y))
                break


class ImageClass:
    def __init__(
        self, canvas, photos_list, object_index, spawn_point, page_class, app_object
    ):
        self.photo = photos_list[object_index]  # PhotoImage object of current image
        self.image = page_class.images_list_original[object_index]  # Current image file
        self.canvas = canvas
        self.page_class = page_class
        self.app_object = app_object
        self.image_id = self.canvas.create_image(
            spawn_point[0], spawn_point[1], image=self.photo
        )

        # Bind the methods for grabbing images and zooming in
        self.canvas.tag_bind(
            self.image_id, "<Button1-Motion>", lambda e: self.move_image(e)
        )
        self.canvas.tag_bind(self.image_id, "<Button-1>", lambda e: self.mouse_click(e))
        self.canvas.tag_bind(self.image_id, "<ButtonRelease-1>", self.mouse_release)
        self.canvas.tag_bind(self.image_id, "<Button-3>", self.full_image)
        self.canvas.tag_bind(self.image_id, "<ButtonRelease-3>", self.full_image_close)

    # Will teleport the image to the closest point inside the canvas if it is outside
    def outofbounds(self):
        self.x_coordinate, self.y_coordinate = self.canvas.coords(self.image_id)

        # Check if the image is not completely inside the canvas for every side
        self.x_coordinate = max(
            self.x_coordinate, self.page_class.image_resolution[0] / 2
        )
        self.y_coordinate = max(
            self.y_coordinate, self.page_class.image_resolution[1] / 2
        )
        self.x_coordinate = min(
            self.x_coordinate,
            self.canvas.winfo_width() - self.page_class.image_resolution[0] / 2,
        )
        self.y_coordinate = min(
            self.y_coordinate,
            self.canvas.winfo_height() - self.page_class.image_resolution[1] / 2,
        )

        self.canvas.coords(self.image_id, self.x_coordinate, self.y_coordinate)

    # Zoom in right-clicked image to fit the entire screen
    def full_image(self, event):
        # Disable image grabbing when zoomed in
        self.canvas.tag_unbind(self.image_id, "<Button1-Motion>")
        self.canvas.tag_unbind(self.image_id, "<Button-1>")
        self.canvas.tag_unbind(self.image_id, "<ButtonRelease-1>")

        self.selected_x, self.selected_y = self.canvas.coords(
            self.image_id
        )  # Remember position of the image
        self.canvas.tag_raise(self.image_id)  # Move image to the front
        self.canvas.coords(
            self.image_id, self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2
        )  # Center image before zooming

        # Zoom image to the max possible size
        self.fulledimage = self.image.resize(self.page_class.full_image_resolution)
        self.fulledimage_photo = ImageTk.PhotoImage(self.fulledimage)
        self.canvas.itemconfig(self.image_id, image=self.fulledimage_photo)

    # Remove fully zoomed image from screen
    def full_image_close(self, event):
        self.canvas.itemconfig(
            self.image_id, image=self.photo
        )  # Set image to original size
        self.canvas.coords(
            self.image_id, self.selected_x, self.selected_y
        )  # Put the image in the position it was before zoom

        # Enable grabbing images again
        self.canvas.tag_bind(
            self.image_id, "<Button1-Motion>", lambda e: self.move_image(e)
        )
        self.canvas.tag_bind(self.image_id, "<Button-1>", lambda e: self.mouse_click(e))
        self.canvas.tag_bind(self.image_id, "<ButtonRelease-1>", self.mouse_release)

    # What happens when an image is released
    def mouse_release(self, event):
        self.canvas.itemconfig(
            self.image_id, image=self.photo
        )  # Return image to original size
        self.outofbounds()  # Check if image is outside of canvas

        # Calculate distance of the image to the closest slot
        self.closest_center = min(
            self.page_class.slot_centers_list,
            key=lambda center: math.dist(center, self.canvas.coords(self.image_id)),
        )

        # Teleport image into slot if close enough
        if (
            math.dist(self.closest_center, self.canvas.coords(self.image_id))
            < self.page_class.image_resolution[1]
        ):
            self.app_object.play_image_release()
            put_in = self.page_class.slot_centers_list.index(
                (self.closest_center[0], self.closest_center[1])
            )

            # If there was no image in the slot previously
            if self.page_class.slotted_image_list[put_in] == 0:
                self.page_class.slotted_image_list[put_in] = self.image_id
                self.canvas.coords(
                    self.image_id, self.closest_center[0], self.closest_center[1]
                )

            # If there already was an image in the slot
            else:
                to_delete = []
                # Find the empty slots from bottom to top. The slots under the image have priority when filling compared to the slots above. If on the same side, the slot closest to the moved image has priority.
                for slot_index, slot_image in reversed(
                    list(enumerate(self.page_class.slotted_image_list))
                ):
                    # Check if is an empty slot
                    if slot_image == 0:
                        # If below, save the slot until a closer one is found
                        if slot_index > put_in:
                            to_delete = [slot_index]
                        # If looking at slots above and an empty slot below has already been found, stop the loop
                        elif len(to_delete) != 0:
                            break
                        # If no empty slots below, stop the loop on the first slot above
                        else:
                            to_delete = [slot_index]
                            break

                # Remove chosen empty slot value and insert the released image
                del self.page_class.slotted_image_list[to_delete[0]], to_delete
                self.page_class.slotted_image_list.insert(put_in, self.image_id)

                # Re-position the images to their new slots
                for image_object in self.page_class.image_objects_list:
                    try:
                        image_slot = self.page_class.slotted_image_list.index(
                            image_object.image_id
                        )
                        self.canvas.coords(
                            image_object.image_id,
                            self.page_class.slot_centers_list[image_slot][0],
                            self.page_class.slot_centers_list[image_slot][1],
                        )
                    except ValueError:
                        continue

        # Play the image_grab audio if image wasn't locked into a slot
        else:
            self.app_object.play_image_grab()

        self.app_object.button_check()

        # Make it possible to zoom in image again
        self.canvas.tag_bind(self.image_id, "<Button-3>", self.full_image)
        self.canvas.tag_bind(self.image_id, "<ButtonRelease-3>", self.full_image_close)

    # Runs when the user left-clicks on an image
    def mouse_click(self, event):
        # Disable zooming in when image is grabbed
        self.canvas.tag_unbind(self.image_id, "<Button-3>")
        self.canvas.tag_unbind(self.image_id, "<ButtonRelease-3>")
        self.app_object.play_image_grab()

        # If the image were in a slot, make it empty
        try:
            to_empty = self.page_class.slotted_image_list.index(self.image_id)
            self.page_class.slotted_image_list[to_empty] = 0
        except ValueError:
            pass

        # Increase the size of the clicked image
        self.selectedimage = self.image.resize(
            (
                int(self.page_class.image_resolution[0] * 1.1),
                int(self.page_class.image_resolution[1] * 1.1),
            )
        )
        self.selectedimage_photo = ImageTk.PhotoImage(self.selectedimage)
        self.canvas.itemconfig(self.image_id, image=self.selectedimage_photo)

        self.canvas.tag_raise(self.image_id)  # Put image in front of every other one
        self.offset = (
            self.canvas.coords(self.image_id)[0] - event.x,
            self.canvas.coords(self.image_id)[1] - event.y,
        )  # Remember the position of the cursor relative to the image when it was clicked

    # Runs when player drags image
    def move_image(self, event):
        self.canvas.coords(
            self.image_id, self.offset[0] + event.x, self.offset[1] + event.y
        )


# Start the program
app = Application()

# Load the window
app.root.mainloop()
