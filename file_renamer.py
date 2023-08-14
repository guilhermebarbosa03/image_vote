import os
import shutil

# Use this script to rename the images so they can be used in the poll
# They will be renamed in batches for each level, with the levels being identified by the number at the end
# All levels need the same number of variations 
# The images have to be sorted first by the level (if there is more than 1) and the variations across all levels need to have the same order.
# For example: level1_variation1, level1_variation2, level2_variation1, level2_variation2 (in this case, there would be 2 levels and 2 image variations per level)
# The images have to be sorted either alphabetically or by creation date for this to work properly

if __name__ == "__main__":

#------------------------------------------- Modify this ---------------------------------------------

    # Path to the images (it should contain only the images you want to rename)
    folder_path = "./images_folder/"

    # Type the name of the variations the levels will have, in the order they are sorted
    variations = ["Sunny","Night","Rain","Snow"]

    # Leave as false if images are sorted alphabetically, True if sorted by date 
    sorted_by_date = False

    # Sorting will be reversed if True (if sorted by date, this will make first level contain the latest images)
    reverse_order = False

    # The folder where the images will be outputted
    output_path = "./renamed_files"

#-----------------------------------------------------------------------------------------------------

def rename(folder_path,variations,sorted_by_date,reverse_order,output_path):
    # Counters for the iterations
    variation_count = 0
    level_count = 1

    total_variations = len(variations)
    filenames = os.listdir(folder_path) # List of files found in the folder

    # Create list sorted by creation date
    if sorted_by_date:
        name_date = [] # List of tuples with file name and creation date
        for filename in filenames:
            date = os.path.getctime(os.path.join(folder_path,filename))
            name_date.append((filename,date))
        name_date.sort(key=lambda x:x[1],reverse=reverse_order) # Sort files and reverse if true
        filenames = [file for file,_ in name_date]
        
    # Create list sorted by name
    else:
        filenames.sort(key=lambda x:os.path.splitext(x)[0],reverse=reverse_order)
        filenames.sort(key=lambda x:len(os.path.splitext(x)[0]),reverse=reverse_order)

    # Add renamed files to output folder
    for filename in filenames:
        new_filename = f"{variations[variation_count]}{level_count}"+os.path.splitext(filename)[1] # Generate the new name of the file: Variation + Level_counter
        os.makedirs(output_path, exist_ok=True)
        shutil.copy(os.path.join(folder_path, filename), os.path.join(output_path,new_filename)) # Copy image to output folder with new name
        # Add to the variation/level counters
        variation_count += 1 
        if variation_count%total_variations == 0:
            variation_count = 0
            level_count +=1

if __name__ == "__main__":
    rename(folder_path,variations,sorted_by_date,reverse_order,output_path)