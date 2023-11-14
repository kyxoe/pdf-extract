from tqdm.auto import tqdm
from PIL import Image
import numpy as np
import cv2, os, img2pdf, fitz, shutil
import tkinter as tk
from tkinter import filedialog
def get_image_list(output_dir):
    images = os.listdir(output_dir)
    images.sort(key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
    image_paths = [os.path.join(output_dir, image) for image in images]
    if not image_paths:
        print("No valid images were processed.")
        return False
    return image_paths


def get_max_image_dimensions(folder_path):
    max_width = 0
    max_height = 0

    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The folder {folder_path} does not exist.")

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            file_path = os.path.join(folder_path, filename)
            image = cv2.imread(file_path)

            if image is not None:
                height, width, _ = image.shape
                max_width = max(max_width, width)
                max_height = max(max_height, height)

    return max_width

def stitch_all(folder_path, image_list):
    images = []
    output_width = get_max_image_dimensions(folder_path=folder_path)
    top_padding = 20
    bottom_padding = 20

    for filename in image_list:
        image = cv2.imread(filename)

        if image is not None:
            current_width = image.shape[1]
            border_width = output_width - current_width
            left_border_width = border_width // 2
            right_border_width = border_width - left_border_width

            canvas_height = image.shape[0] + top_padding + bottom_padding
            canvas = np.ones((canvas_height, output_width, 3), np.uint8) * 255

            # Add the image to the canvas with padding
            canvas[top_padding:top_padding + image.shape[0], left_border_width:left_border_width + current_width, :] = image

            images.append(canvas)
    try:
        combined_image = np.vstack(images)
        return combined_image
    except Exception as e:
        return False



def get_document(image, name):
    # Load the input image using cv2
    output_dir = "output_images"  # Directory to save split images

    split_height = 1555  # Height at which to split the image

    if not image.any():
        print("Error: Image not found.")
        return
    # print(image)
    height, width, channels = image.shape

    # Check if the split height is within the image's height bounds
    if split_height <= 0 or split_height >= height:
        # print("Error: Invalid split height.")
        return

    # Determine the number of splits
    num_splits = height // split_height

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Split the image and save each part
    imgs = []
    start = 0
    split_count = 0

    while start < height:
        end = min(start + split_height, height)
        split_image = image[start:end, :]
        # Save the split image
        output_path = os.path.join(output_dir, f"split_{split_count}.png")
        cv2.imwrite(output_path, split_image)

        # print(f"Saved: {output_path}")
        imgs.append(output_path)
        split_count += 1
        start = end

    
    output_pdf =  f'{name}_notes.pdf'  # Specify the output PDF path

    with open(output_pdf, 'wb') as pdf_output:
        pdf_output.write(img2pdf.convert(imgs))

    print(f"Output Generated -> {output_pdf}")


def process_image(page, counter, output_dir, output_masks):
    # Read the input image
    image_list = page.get_pixmap(matrix = fitz.Matrix(300/72, 300/72))
    image = Image.frombytes("RGB", [image_list.width, image_list.height], image_list.samples)
    image_np = np.array(image)
    image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    with open('values.log') as file:
        lines = file.readlines()

    # Remove leading and trailing whitespaces, then split and convert to integers
    lower_color = tuple(map(int, lines[0].strip()[1:-1].split(', ')))
    upper_color = tuple(map(int, lines[1].strip()[1:-1].split(', ')))

    # Convert to NumPy arrays
    lower_color = np.array(lower_color, dtype=np.uint8)
    upper_color = np.array(upper_color, dtype=np.uint8)

    #Values for test PDF
    lower_color = np.array([40,115, 70], dtype=np.uint8)
    upper_color = np.array([110, 185, 150], dtype=np.uint8)
    # print(lower_color, upper_color)

    # Threshold the image to isolate the specified color
    color_mask = cv2.inRange(image, lower_color, upper_color)

    cv2.imwrite(os.path.join(output_masks, f'colormask_{counter+1}.jpg'), color_mask)

    # Find contours in the thresholded image
    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

    # Loop through identified contours and crop rectangles
    for idx, contour in (enumerate(contours)):
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) == 4 and cv2.contourArea(contour):
            x, y, w, h = cv2.boundingRect(contour)
            if w>400:
                cropped_rectangle = image[y:y + h, x:x + w]

                # Save the cropped rectangle to the output directory
                cv2.imwrite(os.path.join(output_dir, f'page_{counter+1}_{idx}.jpg'), cropped_rectangle)

            else:
                pass

def select_pdf():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    return file_path


if __name__=="__main__":
    if os.path.exists('output'):
        shutil.rmtree('output')
    input_pdf = select_pdf()
    if not input_pdf:
        print('No PDF selected')
        exit()

    name = os.path.splitext(os.path.basename(input_pdf))[0]
    output_dir = os.path.join('output', name)
    output_images = os.path.join(output_dir, 'final_images')
    output_masks = os.path.join(output_dir, 'masks')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_images, exist_ok=True)
    os.makedirs(output_masks, exist_ok=True)
    # print(output_dir, output_masks, output_images)

    pdf_document = fitz.open(input_pdf)
    total_pages = pdf_document.page_count

    for page_number in tqdm(range(total_pages)):
        page = pdf_document.load_page(page_number)
        processed_image = process_image(page, page_number, output_images, output_masks)

    pdf_document.close()

    image_paths = get_image_list(output_images)
    if not image_paths:
        print("No valid images generated. Please check your values.")
        exit()

    combined_image = stitch_all(output_images, image_paths)
    get_document(combined_image, name)
    shutil.rmtree('output')
    if os.path.exists('output_images'):
        shutil.rmtree('output_images')
