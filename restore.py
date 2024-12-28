import os
import replicate
from PIL import Image
import os.path
from tqdm import tqdm
import time
import shutil
import requests

def check_folder_structure():
    """Check and create necessary folders"""
    required_folders = ['photos/bn', 'photos/red', 'colorized', 'gfpgan']
    
    for folder in required_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")

def convert_to_bw(image_path):
    """Convert an image to black and white"""
    with Image.open(image_path) as img:
        bw_image = img.convert('L')
        return bw_image.convert('RGB')

def get_all_images(root_dir):
    """Recursively get all image files from root_dir and its subdirectories"""
    image_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(os.path.join(dirpath, filename))
    return image_files

def colorize_photos():
    """Process and colorize photos from bn and red directories"""
    total_files = 0
    if os.path.exists('photos/bn'):
        total_files += len([f for f in os.listdir('photos/bn') 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    if os.path.exists('photos/red'):
        total_files += len([f for f in os.listdir('photos/red') 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    print(f"\nFound {total_files} images to colorize")
    
    with tqdm(total=total_files, desc="Colorizing images") as pbar:
        # Process photos in 'bn' directory
        if os.path.exists('photos/bn'):
            for filename in os.listdir('photos/bn'):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    input_path = os.path.join('photos/bn', filename)
                    output_path = os.path.join('colorized', f'colorized_{filename}')
                    photos_output_path = os.path.join('photos', f'colorized_{filename}')
                    
                    tqdm.write(f"Processing {filename} from bn folder...")
                    
                    output = replicate.run(
                        "piddnad/ddcolor:ca494ba129e44e45f661d6ece83c4c98a9a7c774309beca01429b58fce8aa695",
                        input={"image": open(input_path, "rb")}
                    )
                    
                    # Download the image from the URL
                    response = requests.get(output)
                    if response.status_code == 200:
                        # Save to colorized folder
                        with open(output_path, "wb") as file:
                            file.write(response.content)
                        
                        # Copy to photos folder for GFPGAN processing
                        shutil.copy2(output_path, photos_output_path)
                    else:
                        tqdm.write(f"Failed to download colorized image for {filename}")
                    
                    pbar.update(1)

        # Process photos in 'red' directory
        if os.path.exists('photos/red'):
            for filename in os.listdir('photos/red'):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    input_path = os.path.join('photos/red', filename)
                    output_path = os.path.join('colorized', f'colorized_{filename}')
                    photos_output_path = os.path.join('photos', f'colorized_{filename}')
                    
                    tqdm.write(f"Processing {filename} from red folder...")
                    
                    bw_image = convert_to_bw(input_path)
                    temp_bw_path = os.path.join('photos/red', f'temp_bw_{filename}')
                    bw_image.save(temp_bw_path)
                    
                    output = replicate.run(
                        "piddnad/ddcolor:ca494ba129e44e45f661d6ece83c4c98a9a7c774309beca01429b58fce8aa695",
                        input={"image": open(temp_bw_path, "rb")}
                    )
                    
                    # Download the image from the URL
                    response = requests.get(output)
                    if response.status_code == 200:
                        # Save to colorized folder
                        with open(output_path, "wb") as file:
                            file.write(response.content)
                        
                        # Copy to photos folder for GFPGAN processing
                        shutil.copy2(output_path, photos_output_path)
                    else:
                        tqdm.write(f"Failed to download colorized image for {filename}")
                    
                    os.remove(temp_bw_path)
                    pbar.update(1)

def restore_photos():
    """Restore photos using GFPGAN"""
    image_files = get_all_images('photos')
    total_files = len(image_files)

    print(f"\nFound {total_files} images to restore")
    
    with tqdm(total=total_files, desc="Restoring photos") as pbar:
        for input_path in image_files:
            relative_path = os.path.relpath(input_path, 'photos')
            output_path = os.path.join('gfpgan', f'restored_{os.path.basename(input_path)}')
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            tqdm.write(f"Restoring {relative_path}...")
            try:
                output = replicate.run(
                    "tencentarc/gfpgan:0fbacf7afc6c144e5be9767cff80f25aff23e52b0708f17e20f9879b2f21516c",
                    input={"img": open(input_path, "rb")}
                )
                
                # Download the image from the URL
                response = requests.get(output)
                if response.status_code == 200:
                    with open(output_path, "wb") as file:
                        file.write(response.content)
                    tqdm.write(f"✓ Successfully restored {relative_path}")
                else:
                    tqdm.write(f"✗ Failed to download restored image for {relative_path}")
            except Exception as e:
                tqdm.write(f"✗ Failed to restore {relative_path}: {str(e)}")
            
            pbar.update(1)

def main():
    print("""
Photo Restoration Suite
======================

This script will:
1. Colorize black & white photos from 'photos/bn/'
2. Convert red-tinted photos from 'photos/red/' to B&W and then colorize them
3. Restore all photos using GFPGAN

Required folder structure:
- photos/
  ├── bn/    (black & white photos)
  └── red/   (red-tinted photos)

Output folders:
- colorized/ (colorized versions)
- gfpgan/    (restored versions)
""")

    # Check and create folders
    check_folder_structure()

    # Colorize photos
    print("\nStep 1: Colorizing photos...")
    colorize_photos()

    # Restore photos
    print("\nStep 2: Restoring photos...")
    restore_photos()

    print("\nProcessing complete! Check the 'colorized' and 'gfpgan' folders for results.")

if __name__ == "__main__":
    main() 