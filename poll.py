import tkinter as tk
from PIL import Image, ImageTk, ImageFile
from tkinter import ttk,filedialog
import pygame
import os
import math
import bisect
import random
import re
import file_renamer

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Base program interface and functionalities
class Application():
    
    def __init__(self):
        # Main window settings
        self.root = tk.Tk()
        self.root.geometry("1280x720")
        self.root.config(bg="#282D2F")
        self.root.minsize(250,200)
        self.root.state("zoomed")
        self.filepath = ""
        self.background_color = "#282D2F"
        self.button_style = {"background":"#515A60","activebackground":"#E0E0E0","foreground":"#FFFFFF","bd":0,"disabledforeground":"#929B91"}
        self.root.update()

        self.start_screen() # Load starting screen
        self.audio_setup()

    # Set up sound effects
    def audio_setup(self):
        pygame.mixer.init()
        self.audio_button_press = pygame.mixer.Sound("./audio/big_tap.mp3")
        self.audio_button_release = pygame.mixer.Sound("./audio/big_tap_end.mp3")
        self.audio_image_grab = pygame.mixer.Sound("./audio/short_tap.mp3")
        self.audio_image_release = pygame.mixer.Sound("./audio/short_tap_low.mp3")
        pygame.mixer.Sound.set_volume(self.audio_button_press,.5)
        pygame.mixer.Sound.set_volume(self.audio_button_release,.7)
        pygame.mixer.Sound.set_volume(self.audio_image_grab,.5)
        pygame.mixer.Sound.set_volume(self.audio_image_release,1.15)

    # Create and load widgets for the start screen
    def start_screen(self):
        # Backgrounds
        self.start_container = tk.Frame(self.root,bg=self.background_color)
        self.folder_container = tk.Frame(self.start_container,bg=self.background_color)

        # Buttons
        self.folder_button = tk.Button(self.folder_container,text="Select Folder",command=self.open_folder,font=("Helvetica",16),**self.button_style)
        self.start_button = tk.Button(self.start_container,text="Start",font=("Helvetica",36),command=self.start_poll,state=tk.DISABLED,**self.button_style)
        self.rename_screen_button = tk.Button(self.root,text="Rename Images",command=self.rename_screen,font=("Helvetica",16),**self.button_style)

        # Warnings
        self.folder_warning = tk.Label(self.start_container,text="Invalid Folder.",bg=self.background_color,fg="red",font=("Helvetica",12))
        self.image_warning = tk.Label(self.start_container,text="The images are not set up properly.\nUse the \"Rename Images\" button at the bottom!",bg=self.background_color,fg="red",font=("Helvetica",12))
        self.file_warning = tk.Label(self.start_container,text="The files in the folder are not valid images.",bg=self.background_color,fg="red",font=("Helvetica",12))

        # Text
        self.title = tk.Label(self.root,background=self.background_color,fg="white",font=("Helvetica",48,"bold"),text="Image Vote")
        self.path_label = tk.Label(self.folder_container,bg=self.background_color,fg="white",font=("Helvetica",12))
        self.rename_label = tk.Label(self.root,text="You have to click here to set up the images!",bg=self.background_color,fg="white",font=("Helvetica",12))
        self.loading_label = tk.Label(self.root,text="Loading...",bg=self.background_color,fg="white",font=("Helvetica",32,"bold"))

        # Load widgets
        self.load_start()

    # Load the starting screen
    def load_start(self):
        self.title.pack(pady=100)
        self.start_container.place(relx=0.5,rely=0.4,anchor="n",width=1024)
        self.folder_container.pack(anchor="center",pady=(0,5),fill="x",expand=True)
        self.folder_button.grid(row=0,column=1)
        self.path_label.grid(row=0,column=0,sticky="e")
        self.folder_container.grid_columnconfigure(0,weight=1,minsize=437)
        self.folder_container.grid_columnconfigure(1,weight=1,minsize=150)
        self.folder_container.grid_columnconfigure(2,weight=1,minsize=437)
        self.start_button.pack(anchor="center")
        self.rename_screen_button.pack(side=tk.BOTTOM,pady=(5,10))
        self.rename_label.pack(side=tk.BOTTOM)

        self.start_button.bind("<ButtonPress-1>", self.play_button_press)
        self.folder_button.bind("<ButtonPress-1>", self.play_button_press)
        self.folder_button.bind("<ButtonRelease-1>", self.play_button_release)
        self.rename_screen_button.bind("<ButtonPress-1>", self.play_button_press)
        self.rename_screen_button.bind("<ButtonRelease-1>", self.play_button_release)

    # Count variations and check if they are consistent for every level
    def count_variations(self):
        variation_dict = {}

        for filename in os.listdir(self.filepath):
            basename = re.sub(r"\d*\.\w+$",r"",filename)
            variation_dict[basename] = variation_dict.get(basename,0) + 1
        variation_values = list(variation_dict.values())

        if len(set(variation_values)) != 1:
            return False
        else:
            return variation_values[0]
        
    # Calculate aspect ratio of the images based on the first one, the rest will be stretched to the same aspect ratio if different 
    def calculate_aspect(self):
        with Image.open(os.path.join(self.filepath,self.imagelist[0])) as img:
            self.base_resolution = img.size
            gcd = math.gcd(self.base_resolution[0],self.base_resolution[1])
            self.aspectratio = (self.base_resolution[0]/gcd,self.base_resolution[1]/gcd)

    # Get the selected folder, removes previous warnings and enable Start Button
    def open_folder(self):
        self.filepath = filedialog.askdirectory()
        self.path_label.config(text=f"Folder: {self.filepath}")

        # Remove warnings
        self.folder_warning.pack_forget()
        self.image_warning.pack_forget()
        self.file_warning.pack_forget()

        # Enable Start Button
        self.start_button.config(state=tk.NORMAL)

    # The page for renaming the images
    def rename_screen(self):
        self.variation_entries = []
        self.variation_labels = []
        self.variation_count = 1
        self.date_sort=False
        self.reverse_sort=False

        # Clear main screen
        self.title.pack_forget()
        self.start_container.place_forget()
        self.rename_screen_button.pack_forget()
        self.rename_label.pack_forget()

        # Create containers for the widgets
        self.rename_container = tk.Frame(self.root,bg=self.background_color)
        self.variation_container = tk.Frame(self.rename_container,bg="#74868f")
        self.variation_labels_container = tk.Frame(self.rename_container,bg=self.background_color)
        self.modify_variation_container = tk.Frame(self.variation_container,bg="#74868f")

        # List with text entries for the variation names
        self.variation_entries.append(tk.Entry(self.variation_container,font=("Helvetica",11),bg=self.button_style["background"],foreground="white",bd=0,insertbackground="white"))
        self.variation_labels.append(tk.Label(self.variation_labels_container,font=("Helvetica",11),bg=self.background_color,foreground="white",text="Variation 1"))

        # Texts
        self.rename_title = tk.Label(self.root,background=self.background_color,fg="white",font=("Helvetica",48,"bold"),text="Rename Images")
        self.rename_disclaimer = tk.Label(self.root,background=self.background_color,fg="white",font=("Helvetica",12,"bold"),text="-The images have to be sorted alphabetically or by creation date, and the variations need to be in the same order for every level\n-If sorted by date, the latest images will be the last level by default")
        self.rename_path_label = tk.Label(self.rename_container,bg=self.background_color,fg="white",font=("Helvetica",11))
        self.reverse_label = tk.Label(self.rename_container,text="Reverse sorting",font=("Helvetica",11),fg="white",bg=self.background_color)
        self.date_sort_label = tk.Label(self.rename_container,text="Sorted by date?",font=("Helvetica",11),fg="white",bg=self.background_color)

        # Warnings
        self.rename_warning = tk.Label(self.root,text="Invalid Folder.",bg=self.background_color,fg="red",font=("Helvetica",11))
        self.empty_entry_warning = tk.Label(self.root,text="Can't have empty variation name.",bg=self.background_color,fg="red",font=("Helvetica",11))
        self.variation_number_incompatible_warning = tk.Label(self.root,text="Number of files needs to be a multiple of the number of variations.",bg=self.background_color,fg="red",font=("Helvetica",11))
        self.successful_rename_warning = tk.Label(self.root,text="Files renamed successfully.",bg=self.background_color,fg="white",font=("Helvetica",11))
        self.error_rename_warning = tk.Label(self.root,text="Error renaming files.",bg=self.background_color,fg="red",font=("Helvetica",11))

        # Buttons
        self.rename_folder_button = tk.Button(self.rename_container,text="Select Folder",**self.button_style,font=("Helvetica",14),command=self.open_folder_rename)
        self.toggle_date_button = tk.Button(self.rename_container,**self.button_style,text="Disabled",font=("Helvetica",12),command=self.toggle_date)
        self.toggle_reverse_button = tk.Button(self.rename_container,**self.button_style,text="Disabled",font=("Helvetica",12),command=self.toggle_reverse)
        self.rename_button = tk.Button(self.rename_container,text="Rename",font=("Helvetica",24),**self.button_style,state=tk.DISABLED,command=self.renaming)
        self.back_button = tk.Button(self.root,**self.button_style,font=("Helvetica",20),text="Back",command=self.go_back_screen)
        self.variation_add_button = tk.Button(self.modify_variation_container,text="Add",font=("Helvetica",10),**self.button_style,command=self.increase_variation)
        self.variation_remove_button = tk.Button(self.modify_variation_container,text="Remove",font=("Helvetica",10),**self.button_style,command=self.decrease_variation)

        # Load the widgets
        self.rename_title.pack(pady=(100,0))
        self.rename_disclaimer.pack(pady=5)
        self.rename_container.pack(pady=(50,5))
        self.rename_folder_button.grid(row=2,column=1,pady=5)
        self.rename_path_label.grid(column=0,row=2,sticky="e")
        self.toggle_date_button.grid(row=1,column=1,pady=5)
        self.toggle_reverse_button.grid(row=0,column=1,pady=5)
        self.date_sort_label.grid(row=1,column=0,sticky="e")
        self.reverse_label.grid(row=0,column=0,sticky="e")
        self.rename_button.grid(row=3,column=1,pady=(50))
        self.back_button.pack(side=tk.BOTTOM,pady=(5,10))
        self.rename_container.grid_columnconfigure(0,weight=1,minsize=437)
        self.rename_container.grid_columnconfigure(1,weight=1,minsize=150)
        self.rename_container.grid_columnconfigure(2,weight=1,minsize=437)
        self.variation_container.grid(row=5,column=1)
        self.variation_labels_container.grid(row=5,column=0,sticky="ne")
        self.variation_entries[0].grid(row=0,column=0,pady=2)
        self.variation_labels[0].grid(row=0,column=0,sticky="ne")
        self.modify_variation_container.grid(row=1,column=0)
        self.variation_add_button.grid(row=0,column=0,pady=2)

        # Bind the sounds for the buttons
        self.rename_folder_button.bind("<ButtonPress-1>",self.play_button_press)
        self.toggle_date_button.bind("<ButtonPress-1>",self.play_button_press)
        self.toggle_reverse_button.bind("<ButtonPress-1>",self.play_button_press)
        self.rename_button.bind("<ButtonPress-1>",self.play_button_press)
        self.variation_add_button.bind("<ButtonPress-1>",self.play_button_press)
        self.variation_remove_button.bind("<ButtonPress-1>",self.play_button_press)
        self.back_button.bind("<ButtonPress-1>",self.play_button_press)
        self.rename_folder_button.bind("<ButtonRelease-1>",self.play_button_release)
        self.toggle_date_button.bind("<ButtonRelease-1>",self.play_button_release)
        self.toggle_reverse_button.bind("<ButtonRelease-1>",self.play_button_release)
        self.rename_button.bind("<ButtonRelease-1>",self.play_button_release)
        self.back_button.bind("<ButtonRelease-1>",self.play_button_release)
        self.variation_add_button.bind("<ButtonRelease-1>",self.play_button_release)
        self.variation_remove_button.bind("<ButtonRelease-1>",self.play_button_release)

    # Get the folder of the files to be renamed
    def open_folder_rename(self):
        self.rename_filepath = filedialog.askdirectory()
        self.rename_path_label.config(text=f"Folder: {self.rename_filepath}")
        self.rename_button.config(state=tk.NORMAL)
        self.successful_rename_warning.pack_forget()

    # Increase the number of variations by 1
    def increase_variation(self):
        self.variation_count += 1

        self.variation_entries.append(tk.Entry(self.variation_container,font=("Helvetica",11),bg=self.button_style["background"],foreground="white",bd=0,insertbackground="white"))
        self.variation_labels.append(tk.Label(self.variation_labels_container,font=("Helvetica",11),bg=self.background_color,foreground="white",text=f"Variation {self.variation_count}"))

        self.variation_entries[-1].grid(row=self.variation_count-1,column=0,pady=2)
        self.variation_labels[-1].grid(row=self.variation_count-1,column=0)

        self.modify_variation_container.grid_configure(row=self.variation_count)

        if self.variation_count == 2:
            self.variation_remove_button.grid(row=0,column=1,padx=(2,0),pady=2)

    # Decrease the number of variations by 1
    def decrease_variation(self):
        self.variation_count -=1

        self.variation_entries[-1].grid_forget()
        del self.variation_entries[-1]
        self.variation_labels[-1].grid_forget()
        del self.variation_labels[-1]

        self.modify_variation_container.grid_configure(row=self.variation_count)

        if self.variation_count == 1:
            self.variation_remove_button.grid_forget()

    # Check if folder, variation count and names are OK and run the rename function
    def renaming(self):
        # Clear main screen
        self.error_rename_warning.pack_forget()
        self.successful_rename_warning.pack_forget()
        self.rename_warning.pack_forget()
        self.empty_entry_warning.pack_forget()
        self.variation_number_incompatible_warning.pack_forget()

        # Check if folder is not valid
        if not self.check_path_valid(self.rename_filepath):
            self.rename_warning.pack()
        # If valid, check if variation names are not empty
        else:
            self.variation_names = [""]*len(self.variation_entries)
            for i,entry in enumerate(self.variation_entries):
                self.variation_names[i] = entry.get()
                if self.variation_names[i] == "":
                    self.empty_entry_warning.pack()
                    return
                # Check if the number of variations is compatible with the number of files
                elif len(os.listdir(self.rename_filepath))%len(self.variation_names) != 0:
                    self.variation_number_incompatible_warning.pack()
                    return
            # Run function to create the renamed files on a new folder
            try:
                file_renamer.rename(self.rename_filepath,self.variation_names,self.date_sort,self.reverse_sort,os.path.join(os.path.abspath(os.curdir),"renamed_files"))

            # Show a warning if there is an error
            except Exception:
                self.error_rename_warning.pack()
            self.successful_rename_warning.pack()
            pass

    # Makes the "sorted by date" button toggleable
    def toggle_date(self):
        if self.toggle_date_button.config('relief')[-1] == 'sunken':
            self.toggle_date_button.config(relief="raised",text="Disabled",bg=self.button_style["background"],fg="white")
            self.date_sort=False
        else:
            self.toggle_date_button.config(relief="sunken",text="Enabled",bg=self.button_style["activebackground"],fg="black")
            self.date_sort=True

    # Makes the "reverse sorting" button toggleable
    def toggle_reverse(self):
        if self.toggle_reverse_button.config('relief')[-1] == 'sunken':
            self.toggle_reverse_button.config(relief="raised",text="Disabled",bg=self.button_style["background"],fg="white")
            self.reverse_sort=False
        else:
            self.toggle_reverse_button.config(relief="sunken",text="Enabled",bg=self.button_style["activebackground"],fg="black")
            self.reverse_sort=True

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
        self.successful_rename_warning.pack_forget()
        self.variation_number_incompatible_warning.pack_forget()

        # Load starting screen
        self.load_start()

    # Check if the folder exists
    def check_path_valid(self,path):
        try:
            listdir = os.listdir(path)
            return listdir
        except FileNotFoundError:
            return False
        
    # Load and start the polls
    def start_poll(self):
        self.play_button_release()
        self.imagelist = self.check_path_valid(self.filepath)

        # Show warning if folder doesn't exist
        if not self.imagelist:
            self.folder_warning.pack()
            return
        
        # Check if all the files are valid images
        for file in self.imagelist:
            try:
                with Image.open(os.path.join(self.filepath,file)) as img:
                    pass
            except:
                self.file_warning.pack()
                return
                
        self.templist = [] # List used to create separated_images list
        self.separated_images = [] # List of lists of images for each page
        self.titledict = {} # Dictionary with the number identifier of the variation and its name
        self.pages = [] # List with objects for each level's page
        self.results = [] # List of lists with the resulting order of image variations for each page

        self.variation_index = 0 # Counter for the variation when creating separated_images list
        self.level_index = 0 # Counter for the level when creating separated_images list
        
        self.current_page = 0 # Number of the current page

        self.calculate_aspect()
        self.total_variations = self.count_variations()

        # Show warning if inconsistent number of variations for the pages
        if not self.total_variations:
            self.image_warning.pack()
            return

        # Clear current screen
        self.title.pack_forget()
        self.start_container.place_forget()
        self.rename_screen_button.pack_forget()
        self.rename_label.pack_forget()
        self.loading_label.place(relx=0.5,rely=0.5,anchor="center")
        
        # Add the images to the separated_list
        for counter in range(len(self.imagelist)):
            if counter < self.total_variations:
                self.titledict[self.variation_index] = re.sub(r"\d*\.\w+$",r"",self.imagelist[self.level_index+self.variation_index*self.total_variations])
            self.templist.append(self.imagelist[self.level_index+self.variation_index*self.total_variations])
            self.variation_index += 1
            if self.variation_index%self.total_variations == 0:
                self.separated_images.append(self.templist)
                self.templist = []
                self.level_index += 1
                self.variation_index = 0

        # Create dictionary with the number id of the variations and their current score    
        self.pointdict = {i:0 for i in range(self.total_variations)}

        # Load the page levels
        for count,page in enumerate(self.separated_images):
            self.pages.append(Level(self,page))
            self.pages[count].canvas.pack_forget()

        self.last_page_index = len(self.pages) - 1
        
        self.next_button = tk.Button(self.root, text="Next",font=("Helvetica",24),borderwidth=0,fg="#FFFFFF",disabledforeground="#888888", command=self.show_next_page,activebackground="#D0D0D0")
        self.next_button.pack(side="right",fill="y")
        self.update_button()
        self.show_page(0) # Show the first level

        self.next_button.bind("<ButtonPress-1>", self.play_button_press) # Bind sound to the "Next" button

    # Play audio when pressing button
    def play_button_press(self,event=None):
        self.audio_button_press.play()

    # Play audio when releasing button
    def play_button_release(self,event=None):
        self.audio_button_release.play()

    # Hide current page and show the next one
    def show_page(self, page_number):
        self.pages[self.current_page].canvas.pack_forget() # Hide current page
        self.current_page = page_number # Update page index
        self.pages[self.current_page].canvas.pack(anchor="nw",side=tk.LEFT,fill="both",expand=True) # Load next page
        # Update next page data
        self.pages[self.current_page].canvas.update()
        self.pages[self.current_page].adjust_sizes() 
        self.update_button()
        self.root.config(bg=self.pages[self.current_page].color)
        
    # Update the 'Next' button
    def update_button(self):
        self.next_button.config(bg=self.pages[self.current_page].color) # Change color to fit the current page
        self.next_button.config(state=tk.DISABLED) # Disable button
        if self.current_page == self.last_page_index: 
            self.next_button.config(command=lambda:self.finish_game()) # Load final screen if in the last page

    # Save current page results and run show_page
    def show_next_page(self):
        self.play_button_release()
        self.results.append(self.image_order_list) # Save current page results
        if self.current_page < self.last_page_index:
            self.show_page(self.current_page + 1)

    # Enable button if all slots are filled
    def button_check(self):
        self.image_order_list = list(dict(sorted(self.pages[self.current_page].image_position_dict.items(),key=lambda x: x[0])).values()) # Create list of the images sorted by their position
        if len(self.image_order_list) == self.total_variations:
            self.next_button.config(state=tk.NORMAL)
        else:
            self.next_button.config(state=tk.DISABLED)

    # Calculate ranking results and show final screen
    def finish_game(self):
        self.play_button_release()
        self.results.append(self.image_order_list) # Save last page results
        # Switch next button for a finish button
        self.next_button.pack_forget()
        self.end_button = tk.Button(self.root, text="Finish",font=("Helvetica",24),borderwidth=0,width=6,bg="#515A60",fg="#FFFFFF",command=lambda:self.root.destroy(),activebackground="#D0D0D0")
        self.end_button.pack(side=tk.RIGHT,fill="y")

        # Bind audio to the last button
        self.end_button.bind("<ButtonPress-1>", self.play_button_press)
        self.end_button.bind("<ButtonRelease-1>", self.play_button_release)

        self.calculate_score()
        self.ranking_screen()

    # Calculate the score of each variation
    def calculate_score(self):
        for pageresult in self.results:
            for subtractor,identifier in enumerate(pageresult):
                self.pointdict[identifier-2-math.ceil(self.total_variations/2)] += 4-subtractor
        self.finaldict = {self.titledict[key[0]]:self.pointdict[key[0]] for key in sorted(self.pointdict.items(),key=lambda item: -item[1])}

    # Adjust size of the scroll region of the ranking list when resizing window
    def ranking_configure(self,event):
        self.rankingcanvas.itemconfig(1,width=self.rankingcanvas.winfo_width())
        if self.canvasgrid.bbox("all")[3] > self.rankingcanvas.winfo_height():
            self.rankingcanvas.configure(scrollregion=(0,0,self.canvasgrid.bbox("all")[2],self.canvasgrid.bbox("all")[3]))
        else:
            self.rankingcanvas.configure(scrollregion=(0,0,self.canvasgrid.bbox("all")[2],self.rankingcanvas.winfo_height()))

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
        self.rankingcanvas = tk.Canvas(self.rankingframe,bg="#383D3F",highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.rankingframe,orient="vertical",command=self.rankingcanvas.yview(),bg="#50565B",troughcolor="#383D3F")
        self.canvasgrid = tk.Frame(self.rankingcanvas,bg="#50565B")

        # Load the widgets
        self.rankingframe.pack(anchor=tk.CENTER,fill=tk.BOTH,expand=True,padx=250,pady=50)
        self.rankingcanvas.pack(side=tk.LEFT,expand=True,fill="both",padx=0)
        self.scrollbar.pack(side=tk.RIGHT,fill="y")
        self.rankingcanvas.config(yscrollcommand=self.scrollbar.set)
        self.rankingcanvas.update()
        self.rankingcanvas.create_window(4,4,window=self.canvasgrid,anchor="nw",width=self.rankingcanvas.winfo_width()-8)
        # Load variation names and scores
        contestant_index = 0
        for contestant,point in self.finaldict.items():
            self.canvasgrid.columnconfigure(0,weight=1)
            self.separator.append(ttk.Separator(self.canvasgrid, orient="horizontal"))
            self.horizontalseparatorlist.append(tk.Frame(self.canvasgrid,bg="#50565B"))
            self.contestantnamelist.append(tk.Label(self.horizontalseparatorlist[contestant_index],text=contestant,font=("Helvetica",24),background="#50565B",foreground="#E0E0E0"))
            self.contestantpointlist.append(tk.Label(self.horizontalseparatorlist[contestant_index],text=(f"Score: {point}"),font=("Helvetica",24),background="#50565B",foreground="#E0E0E0"))
            self.horizontalseparatorlist[contestant_index].grid(row=contestant_index*2,sticky="we")
            self.contestantnamelist[contestant_index].pack(padx=10,side=tk.LEFT)
            self.contestantpointlist[contestant_index].pack(side=tk.RIGHT,padx=10)
            self.separator[contestant_index].grid(row=(contestant_index*2+1),column=0,sticky="we")
            self.canvasgrid.rowconfigure(contestant_index*2,weight=1,minsize=75)
            contestant_index+=1
        
        self.rankingcanvas.bind_all('<MouseWheel>', lambda e: self.rankingcanvas.yview_scroll(int(-1*(e.delta/60)), 'units'))
            
        self.separator[-1].destroy()

        # Adjust scroll region size
        if self.canvasgrid.bbox("all")[3] > self.rankingcanvas.winfo_height():
            self.rankingcanvas.configure(scrollregion=(0,0,self.canvasgrid.bbox("all")[2],self.canvasgrid.bbox("all")[3]))
        else:
            self.rankingcanvas.configure(scrollregion=(0,0,self.canvasgrid.bbox("all")[2],self.rankingcanvas.winfo_height()))
            
        self.rankingcanvas.bind("<Configure>",self.ranking_configure)

    # Close the app when finished
    def close_app(self):
        self.root.destroy()


# Class for the pages of the levels
class Level():

    def __init__(self,app_object,page_images):
        
        self.image_position_dict = {} # Dictionary with slot coordinate and the id of the image they contain
        self.image_slot_dict = {} # Dictionary with all images and the number of the slot they are in
        self.photos_list = [] # List of ImageTk.PhotoImage objects of the resized images
        self.photos_list_resized = [] # List of ImageTk.PhotoImage objects
        self.images_list_original = [] # List of the images with their original size
        self.images_list_resized = [] # List of the images after resizing to fit in the slots
        self.image_object = [] # List with all objects of each image of the page
        self.spawnpoint_list = [(0,0)] # List of generated spawn coordinates for each image of the page
        self.app_object = app_object # Application class object
        self.page_images = page_images # List with the images of the current page

        # Creating and loading page widgets
        self.canvas = tk.Canvas(self.app_object.root, bg="#282D2F", highlightthickness=0)
        self.canvas.pack(anchor="nw",side=tk.LEFT,padx=(0,50),fill="both")
        self.app_object.start_container.lift()
        self.canvas.update()
        self.slot_background = self.canvas.create_rectangle(0,0,1,1)
        self.slot_border = [self.canvas.create_rectangle(0,0,1,1) for _ in range(math.ceil(self.app_object.total_variations/2))]

        self.calculate_size()
        self.spawn_images()

        self.canvas.itemconfig(self.slot_background,fill=self.color)
        self.tooltip = tk.Label(self.canvas,background=self.bright_color,foreground="#FFFFFF",text="Drag images with left-click\nRight-click on images to zoom in\nThe higher the image, the higher the score",font=("Helvetica",10,"bold"))
        self.tooltip.place(x=20,y=20)
        self.canvas.update()
        self.canvas.focus_set()
        self.canvas.bind('<Configure>',lambda e:self.calculate_size(e,True))
        
    # Load the image files into image objects and get color for the background
    def spawn_images(self):
        for x,imagefile in enumerate(self.page_images):
            self.spawn_random()
            self.images_list_original.append(Image.open(os.path.join(self.app_object.filepath,imagefile)))
            self.images_list_resized.append(self.images_list_original[x].resize((self.image_resolution[0],self.image_resolution[1])))
            self.photos_list.append(ImageTk.PhotoImage(self.images_list_resized[x]))
            self.image_object.append(ImageClass(self.canvas,self.photos_list,x,self.spawnpoint_list[x+1],self.empty_slots_coords,self,self.app_object,self.slot_centers_list))

        # Get the average color of one of the page's images to set as background
        self.colorgetter = self.images_list_resized[0].resize((1,1))
        self.avg_color = self.colorgetter.getpixel((0,0))
        self.color = (f'#{int(self.avg_color[0]*0.75):02x}{int(self.avg_color[1]*0.75):02x}{int(self.avg_color[2]*0.75):02x}')
        self.bright_color = (f'#{self.avg_color[0]:02x}{self.avg_color[1]:02x}{self.avg_color[2]:02x}')
        self.canvas.config(bg=self.bright_color)

    # Calculate the maximum size available for the images at the current window size
    def calculate_size(self,event=None,re_size=False):
        resvertical = min(self.canvas.winfo_height()/self.app_object.total_variations,self.app_object.base_resolution[1])
        reshorizontal = min(self.canvas.winfo_width(),self.app_object.base_resolution[0])
        bottleneck = min(resvertical*self.app_object.aspectratio[0],reshorizontal*self.app_object.aspectratio[1])
        self.image_resolution = (math.floor((bottleneck/self.app_object.aspectratio[1])),math.floor(bottleneck/self.app_object.aspectratio[0]))
        self.adjust_sizes()
        if re_size:
            self.re_size()

    # Change info about the coordinates of the slots and resolutions
    def adjust_sizes(self):
        self.slot_centers_list = [(float((self.canvas.winfo_width())/2),self.image_resolution[1]*x + self.image_resolution[1]/2) for x in range(self.app_object.total_variations)]

        for i,slot in enumerate(self.slot_border):
            self.canvas.coords(slot,(self.canvas.winfo_width()-self.image_resolution[0])/2,0+i*2*self.image_resolution[1],(self.canvas.winfo_width()+self.image_resolution[0])/2,self.image_resolution[1]+i*2*self.image_resolution[1])
        self.canvas.coords(self.slot_background,(self.canvas.winfo_width()-self.image_resolution[0])/2,0,(self.canvas.winfo_width()+self.image_resolution[0])/2,self.app_object.root.winfo_height())
        self.empty_slots_coords = [self.slot_centers_list[i] for i in range(self.app_object.total_variations) if i not in self.image_slot_dict.values()]

        for i,img in enumerate(self.image_object):
            img.update_arguments(self.empty_slots_coords,self.slot_centers_list,self.image_resolution)
            if i+2+len(self.slot_border) in self.image_position_dict.values():
                self.canvas.coords(i+2+len(self.slot_border),self.slot_centers_list[self.image_slot_dict[i+2+len(self.slot_border)]][0],self.slot_centers_list[self.image_slot_dict[i+2+len(self.slot_border)]][1])

            img.outofbounds()

    # Change size of the images
    def re_size(self):
        self.photos_list_resized.clear()
        
        # If the new image size hasn't been loaded yet, it will use the original size as the base to not lose sharpness, but this is laggier
        if self.image_resolution[0] > self.images_list_resized[0].size[0]:
            for i,img in enumerate(self.images_list_resized):
                self.images_list_resized[i] = self.images_list_original[i].resize((self.image_resolution[0],self.image_resolution[1]))
                self.photos_list_resized.append(ImageTk.PhotoImage(self.images_list_resized[i]))
                self.image_object[i].photo = self.photos_list_resized[i] 
                self.canvas.itemconfig(self.image_object[i].image_id,image=self.photos_list_resized[i])
        # Uses resized images as the base for the resizing (less lag)
        else:
            for i,img in enumerate(self.images_list_resized):
                img = img.resize((self.image_resolution[0],self.image_resolution[1]))
                self.photos_list_resized.append(ImageTk.PhotoImage(img))
                self.image_object[i].photo = self.photos_list_resized[i]
                self.canvas.itemconfig(self.image_object[i].image_id,image=self.photos_list_resized[i])

    # Calculate the spawn coordinates randomly for one image
    def spawn_random(self):
        # Define if image will be on left or right side
        while True:
            if random.randint(0,1)%2 == 0:
                self.spawn_point_x = random.randint(int(self.image_resolution[0]*2+self.image_resolution[0]),int(self.image_resolution[0]*4-self.image_resolution[0]/2))
            else:
                self.spawn_point_x = random.randint(int(self.image_resolution[0]/2),int(self.image_resolution[0]*2-self.image_resolution[0]))

            self.spawn_point_y = random.randint(int(self.image_resolution[1]/2),int(self.image_resolution[1]*self.app_object.total_variations-self.image_resolution[1]/2))

            # Check if images are far enough apart for each other
            self.distances = [math.dist((self.spawn_point_x,self.spawn_point_y),p) for p in self.spawnpoint_list]
            if min(self.distances) > self.image_resolution[1]:
                self.spawnpoint_list.append((self.spawn_point_x,self.spawn_point_y))
                break

    # Update dictionary with the image slots
    def update_results(self):
        self.image_position_dict = {self.canvas.coords(widget_id)[1]:widget_id for widget_id in self.canvas.find_all() if tuple(self.canvas.coords(widget_id)) in self.slot_centers_list}
        self.image_slot_dict = {dictiteration[1]:self.slot_centers_list.index((self.slot_centers_list[0][0],dictiteration[0])) for dictiteration in self.image_position_dict.items()}
            

class ImageClass():
    def __init__(self,canvas,photos_list,object_index,spawn_point,empty_slots_coords,page_class,app_object,slot_centers_list):

        self.slot_centers_list = slot_centers_list # List with the coordinates of the center of all slots
        self.photo = photos_list[object_index] # PhotoImage object of current image
        self.image = page_class.images_list_original[object_index] # Current image file
        self.canvas = canvas
        self.page_class = page_class
        self.empty_slots_coords = empty_slots_coords
        self.app_object = app_object
        self.image_id = self.canvas.create_image(spawn_point[0],spawn_point[1],image=self.photo)
        self.image_resolution = self.page_class.image_resolution

        # Bind the methods for grabbing images and zooming in
        self.canvas.tag_bind(self.image_id, '<Button1-Motion>', lambda e: self.move_image(e))
        self.canvas.tag_bind(self.image_id, '<Button-1>', lambda e: self.mouse_click(e))
        self.canvas.tag_bind(self.image_id, '<ButtonRelease-1>', self.mouse_release)
        self.canvas.tag_bind(self.image_id, '<Button-3>', self.full_image)
        self.canvas.tag_bind(self.image_id, '<ButtonRelease-3>', self.full_image_close)


    # Update info about the resolutions, sizes, slots coordinates after resizing
    def update_arguments(self,empty_slots_coords,slot_centers_list,image_resolution):
        self.empty_slots_coords = empty_slots_coords
        self.slot_centers_list = slot_centers_list
        self.image_resolution = image_resolution

        fullvertical = self.canvas.winfo_height()
        fullhorizontal = self.canvas.winfo_width()
        bottleneck = min(fullvertical*self.app_object.aspectratio[0],fullhorizontal*self.app_object.aspectratio[1])
        self.full_image_resolution = (math.floor((bottleneck/self.app_object.aspectratio[1])),math.floor(bottleneck/self.app_object.aspectratio[0]))

    # Will teleport the image to the closest point inside the canvas if it is outside
    def outofbounds(self):

        self.repositioned_x,self.repositioned_y = self.canvas.coords(self.image_id)

        # Check if the image is not completely inside the canvas for every side
        self.repositioned_x = max(self.repositioned_x, self.image_resolution[0]/2)
        self.repositioned_y = max(self.repositioned_y, self.image_resolution[1]/2)
        self.repositioned_x = min(self.repositioned_x, self.canvas.winfo_width()-self.image_resolution[0]/2)
        self.repositioned_y = min(self.repositioned_y, self.canvas.winfo_height()-self.image_resolution[1]/2)

        self.canvas.coords(self.image_id,self.repositioned_x,self.repositioned_y)

    # Zoom in right-clicked image to fit the entire screen
    def full_image(self,event):
        # Disable image grabbing when zoomed in
        self.canvas.tag_unbind(self.image_id, '<Button1-Motion>')
        self.canvas.tag_unbind(self.image_id, '<Button-1>')
        self.canvas.tag_unbind(self.image_id, '<ButtonRelease-1>')

        self.selected_x,self.selected_y = self.canvas.coords(self.image_id) # Remember position of the image
        self.canvas.tag_raise(self.image_id) # Move image to the front
        self.canvas.coords(self.image_id,self.canvas.winfo_width()/2,self.canvas.winfo_height()/2) # Center image before zooming

        # Zoom image to the max possible size
        self.fulledimage = self.image.resize(self.full_image_resolution)
        self.fulledimage_photo = ImageTk.PhotoImage(self.fulledimage)
        self.canvas.itemconfig(self.image_id,image=self.fulledimage_photo)

    # Remove fully zoomed image from screen
    def full_image_close(self,event):
        self.canvas.itemconfig(self.image_id,image=self.photo) # Set image to original size
        self.canvas.coords(self.image_id,self.selected_x,self.selected_y) # Put the image in the position it was before zoom

        # Enable grabbing images again
        self.canvas.tag_bind(self.image_id, '<Button1-Motion>', lambda e: self.move_image(e))
        self.canvas.tag_bind(self.image_id, '<Button-1>', lambda e: self.mouse_click(e))
        self.canvas.tag_bind(self.image_id, '<ButtonRelease-1>', self.mouse_release)


    # What happens when an image is released
    def mouse_release(self,event):
        self.canvas.itemconfig(self.image_id,image=self.photo) # Return image to original size
        self.outofbounds() # Check if image is outside of canvas

        # Calculate distance of the image to the closest slot
        self.distances = [math.dist(p,self.canvas.coords(self.image_id)) for p in self.slot_centers_list]
        self.closest_center = self.slot_centers_list[self.distances.index(min(self.distances))]
        self.page_class.update_results()

        # Teleport image into slot if close enough
        if min(self.distances) < self.image_resolution[1]:
            self.app_object.audio_image_release.play()
            self.canvas.coords(self.image_id,self.closest_center[0],self.closest_center[1])

            # If there already was an image in the slot 
            if self.canvas.coords(self.image_id)[1] in self.page_class.image_position_dict.keys() and self.image_id != self.page_class.image_position_dict[self.canvas.coords(self.image_id)[1]]:

                # If the there are no empty slots below, move previous image up
                if self.canvas.coords(self.page_class.image_position_dict[self.canvas.coords(self.image_id)[1]])[1] > self.empty_slots_coords[-1][1]:
                    self.imagesbelow = [x for x in sorted(self.page_class.image_position_dict.keys(),reverse=True) if x < self.canvas.coords(self.image_id)[1] and (self.canvas.coords(self.image_id)[0],x) in self.slot_centers_list]
                    self.previous = self.canvas.coords(self.image_id)[1]
                    self.group = []

                    # Find all images below (that are not separated by an empty slot) to move down
                    for counter,imagebelow in enumerate(self.imagesbelow):
                        if (self.canvas.coords(self.image_id)[1] - imagebelow) == self.image_resolution[1]*(counter+1):
                            self.group.append(imagebelow)
                        else:
                            break


                    self.emptybelow = [x for x in reversed(self.empty_slots_coords) if x[1] < self.canvas.coords(self.image_id)[1]] # Find all empty slots below 

                    # Iterate through each image to move down
                    while len(self.group) > 0:
                        self.beforemoved = self.canvas.coords(self.page_class.image_position_dict[self.group[-1]])
                        self.canvas.coords(self.page_class.image_position_dict[self.group[-1]],self.emptybelow[0][0],self.emptybelow[0][1])
                        bisect.insort(self.empty_slots_coords, tuple(self.beforemoved),key=lambda z:z[1])

                        self.empty_slots_coords.remove(tuple(self.canvas.coords(self.page_class.image_position_dict[self.group[-1]])))
                        self.emptybelow = [z for z in reversed(self.empty_slots_coords) if z[1] < self.canvas.coords(self.image_id)[1]]
                        self.group.pop()

                    # Move the last image (was previously in the slot the new image took)
                    self.empty_slots_coords.remove(self.emptybelow[0])
                    self.canvas.coords(self.page_class.image_position_dict[self.canvas.coords(self.image_id)[1]],self.emptybelow[0][0],self.emptybelow[0][1])
                    self.emptybelow.clear()


                # If there are any empty slots below, move the previous image down. If there is an image where the previous one moved to, it will also be moved down
                else:
                    self.imagesbelow = [x for x in sorted(self.page_class.image_position_dict.keys()) if x > self.canvas.coords(self.image_id)[1] and (self.canvas.coords(self.image_id)[0],x) in self.slot_centers_list]
                    self.previous = self.canvas.coords(self.image_id)[1]
                    self.group = []

                    # Find all images below (that are not separated by an empty slot) to move down
                    for counter,imagebelow in enumerate(self.imagesbelow):
                        if (imagebelow - self.canvas.coords(self.image_id)[1]) == self.image_resolution[1]*(counter+1):
                            self.group.append(imagebelow)
                        else:
                            break


                    self.emptybelow = [x for x in self.empty_slots_coords if x[1] > self.canvas.coords(self.image_id)[1]] # Find all empty slots below 

                    # Iterate through each image to move down
                    while len(self.group) > 0:
                        self.beforemoved = self.canvas.coords(self.page_class.image_position_dict[self.group[-1]])
                        self.canvas.coords(self.page_class.image_position_dict[self.group[-1]],self.emptybelow[0][0],self.emptybelow[0][1])
                        bisect.insort(self.empty_slots_coords, tuple(self.beforemoved),key=lambda z:z[1])

                        self.empty_slots_coords.remove(tuple(self.canvas.coords(self.page_class.image_position_dict[self.group[-1]])))
                        self.emptybelow = [z for z in self.empty_slots_coords if z[1] > self.canvas.coords(self.image_id)[1]]
                        self.group.pop()

                    # Move the last image (was previously in the slot the new image took)
                    self.empty_slots_coords.remove(self.emptybelow[0])
                    self.canvas.coords(self.page_class.image_position_dict[self.canvas.coords(self.image_id)[1]],self.emptybelow[0][0],self.emptybelow[0][1])
                    self.emptybelow.clear()

            # Remove slot the image was put in from list of empty slots
            else:
                self.empty_slots_coords.remove(tuple(self.canvas.coords(self.image_id)))
        
        # Play the image_grab audio if image wasn't locked into a slot
        else:
            self.app_object.audio_image_grab.play()
            
        self.page_class.update_results()
        self.app_object.button_check()

        # Make it possible to zoom in image again
        self.canvas.tag_bind(self.image_id, '<Button-3>', self.full_image)
        self.canvas.tag_bind(self.image_id, '<ButtonRelease-3>', self.full_image_close)

    # Runs when the user left-clicks on an image
    def mouse_click(self,event):
        # Disable zooming in when image is grabbed
        self.canvas.tag_unbind(self.image_id, '<Button-3>')
        self.canvas.tag_unbind(self.image_id, '<ButtonRelease-3>')
        self.app_object.audio_image_grab.play()
        # Add slot it was in to the list of empty slots
        if tuple(self.canvas.coords(self.image_id)) in self.slot_centers_list:
            bisect.insort(self.empty_slots_coords, tuple(self.canvas.coords(self.image_id)),key= lambda z:z[1])

        # Increase the size of the clicked image 
        self.selectedimage = self.image.resize((int(self.image_resolution[0]*1.1),int(self.image_resolution[1]*1.1)))
        self.selectedimage_photo = ImageTk.PhotoImage(self.selectedimage)
        self.canvas.itemconfig(self.image_id,image=self.selectedimage_photo) 

        self.canvas.tag_raise(self.image_id) # Put image in front of every other one
        self.offset = (self.canvas.coords(self.image_id)[0]-event.x,self.canvas.coords(self.image_id)[1]-event.y) # Remember the position of the cursor relative to the image when it was clicked

    # Runs when player drags image
    def move_image(self, event):
        self.canvas.coords(self.image_id, self.offset[0]+event.x,self.offset[1]+event.y)

# Start the program
app = Application()

# Load the window
app.root.mainloop()