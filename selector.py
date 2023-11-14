import cv2
import numpy as np
from tkinter import Tk, filedialog
from pynput import keyboard, mouse
from PIL import Image, ImageGrab
import tkinter as tk
from tkinter import ttk, Label
import threading
import fitz

class ColorPickerApp:
    value_logger = []  # Class variable to store color values

    def __init__(self):
        self.color_picker_enabled = False

        # Create the main window
        self.root = tk.Tk()
        self.root.title("Color Picker")

        # Create GUI elements
        self.status_label = Label(self.root, text="Status : ")
        self.status_label.grid(row=0, column=0, padx=2, pady=10)

        self.color_picker_button = ttk.Button(self.root, text="Off", command=self.toggle_color_picker)
        self.color_picker_button.grid(row=1, column=0, padx=10, pady=10)

        self.info_label = ttk.Label(self.root, text="Click above to turn on")
        self.info_label.grid(row=2, column=0, padx=10, pady=10)

        self.rgb_label = ttk.Label(self.root, text="")
        self.rgb_label.grid(row=3, column=0, padx=10, pady=10)

        self.color_display = Label(self.root, text="", bg='#F0F0F0', width=5, height=5)
        self.color_display.grid(row=4, column=0, padx=10, pady=10)

        self.exit_button = ttk.Button(self.root, text="Done", command=self.exit_app)
        self.exit_button.grid(row=5, column=0, padx=10, pady=10)

        # Set up keyboard and mouse listeners in a separate thread
        self.listener_thread = threading.Thread(target=self.start_listeners, daemon=True)
        self.listener_thread.start()

    def start_listeners(self):
        with keyboard.Listener(on_release=self.on_release) as klstnr:
            with mouse.Listener(on_click=self.on_click) as mlstnr:
                klstnr.join()
                mlstnr.join()

    def toggle_color_picker(self):
        self.color_picker_enabled = not self.color_picker_enabled
        if self.color_picker_enabled:
            self.info_label.config(text="Please click on the color pixel.")
            self.color_picker_button.config(text="On")
        else:
            self.info_label.config(text="Click above to turn on")
            self.color_picker_button.config(text="Off")

    def on_click(self, x, y, button, pressed):
        if self.color_picker_enabled and pressed and button == mouse.Button.left:
            try:
                self.check_color(x, y)
            except Exception as e:
                print(f"Error while checking color: {e}")

    def check_color(self, x, y):
        bbox = (x, y, x + 1, y + 1)
        im = ImageGrab.grab(bbox=bbox)
        rgbim = im.convert('RGB')
        r, g, b = rgbim.getpixel((0, 0))
        output = f'COLOR: rgb{(r, g, b)} | HEX #{self.get_hex((r, g, b))}\n'
        self.color_display.config(bg=f"#{self.get_hex((r, g, b))}")
        self.rgb_label.config(text=output)
        self.__class__.value_logger.append((b, g, r))

    def get_hex(self, rgb):
        return '%02X%02X%02X' % rgb

    def on_release(self, key):
        if key == keyboard.Key.esc:
            self.root.destroy()

    def exit_app(self):
        # ... (file handling code if uncommented)
        self.color_picker_enabled = False
        self.root.destroy()

    @classmethod
    def get_value_logger(cls):
        if len(cls.value_logger) == 0:
            print("Nothing selected")
        elif len(cls.value_logger) == 1:
            return cls.value_logger[0]
        else:
            return cls.value_logger[-2]

def resize_image(clean_image):
    screen_height, screen_width = 720, 1080  # Adjust the screen_height as needed
    window_height, window_width = clean_image.shape[:2]

    if window_height > screen_height:
        # Calculate the width to maintain the aspect ratio
        aspect_ratio = window_width / window_height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
        clean_image = cv2.resize(clean_image, (new_width, new_height))
    return clean_image

def process_image(image, lower, upper):
    mask = cv2.inRange(image, lower, upper)
    return mask

def on_slider_change(x):
    # Get current slider values
    lower = (cv2.getTrackbarPos('Lower B', 'Trackbars'),
                   cv2.getTrackbarPos('Lower G', 'Trackbars'),
                   cv2.getTrackbarPos('Lower R', 'Trackbars'))
    upper = (cv2.getTrackbarPos('Upper B', 'Trackbars'),
                   cv2.getTrackbarPos('Upper G', 'Trackbars'),
                   cv2.getTrackbarPos('Upper R', 'Trackbars'))

    # Process the image with the updated values
    mask = process_image(image, lower, upper)
    resized_mask = resize_image(mask)
    resized_image = resize_image(image)

    colored_mask = cv2.cvtColor(resized_mask, cv2.COLOR_GRAY2BGR)
    combined = np.hstack((resized_image, colored_mask))

    # return (lower, upper, resized)
    # Show the processed image
    cv2.imshow('Only white rectangle should be visible', combined)

    # cv2.imshow('Only Rectangle Should be Visible', resized_mask)


def create_trackbars():
    cv2.createTrackbar('Lower B', 'Trackbars', 0, 255, on_slider_change)
    cv2.createTrackbar('Lower G', 'Trackbars', 0, 255, on_slider_change)
    cv2.createTrackbar('Lower R', 'Trackbars', 0, 255, on_slider_change)

    cv2.createTrackbar('Upper B', 'Trackbars', 0, 255, on_slider_change)
    cv2.createTrackbar('Upper G', 'Trackbars', 0, 255, on_slider_change)
    cv2.createTrackbar('Upper R', 'Trackbars', 0, 255, on_slider_change)

    cv2.setTrackbarPos('Lower B', 'Trackbars', init_lower[0])
    cv2.setTrackbarPos('Lower G', 'Trackbars', init_lower[1])
    cv2.setTrackbarPos('Lower R', 'Trackbars', init_lower[2])

    cv2.setTrackbarPos('Upper B', 'Trackbars', init_upper[0])
    cv2.setTrackbarPos('Upper G', 'Trackbars', init_upper[1])
    cv2.setTrackbarPos('Upper R', 'Trackbars', init_upper[2])


def get_final_values():
    # Get current slider values
    lower = (cv2.getTrackbarPos('Lower B', 'Trackbars'),
                   cv2.getTrackbarPos('Lower G', 'Trackbars'),
                   cv2.getTrackbarPos('Lower R', 'Trackbars'))
    upper = (cv2.getTrackbarPos('Upper B', 'Trackbars'),
                   cv2.getTrackbarPos('Upper G', 'Trackbars'),
                   cv2.getTrackbarPos('Upper R', 'Trackbars'))
    # print(f"Lower BGR - {lower}\nUpper BGR - {upper}")
    with open('values.log', 'w') as f:
        f.write(f"{lower}\n")
        f.write(f"{upper}")


def choose_image():
    rootx = Tk()
    rootx.withdraw()  # Hide the main window

    file_path = filedialog.askopenfilename(title="Select an image file",
                                           filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp")])
    
    if file_path:
        return cv2.imread(file_path)
    else:
        return None

def select_pdf():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    return file_path

def get_bounds(values):
    b, g ,r = values 
    lower = [b-40, g-40, r-40]
    upper = [b+10, g+10, r+10]
    l_clip=[max(0,min(value, 255)) for value in lower]
    u_clip=[max(0,min(value, 255)) for value in upper]
    lower_arr = np.array(l_clip, dtype=np.uint8)
    upper_arr = np.array(u_clip, dtype=np.uint8)
    return (lower_arr, upper_arr)


def show_instruction(img):

    border_color = [255, 255, 255]  # White color
    border_size = 40  # Adjust as needed

    # Create a white strip
    white_strip = np.ones((border_size, img.shape[1], 3), dtype=np.uint8) * border_color

    # Stack the white strip on top of the image
    img_with_strip = np.vstack((white_strip, img))

    # Add text to the image
    text_lines = [
        "Find Image with box",
        "   Press Enter to Select",
        "   Press L to Next Image"
    ]

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 2
    font_color = (0, 0, 0)  # Black color
    text_position = (10, 10)  # Adjust the starting position as needed

    for text_line in text_lines:
        cv2.putText(
            img_with_strip, text_line,
            text_position, font, font_scale,
            font_color, font_thickness, cv2.LINE_AA
        )
        text_position = (text_position[0], text_position[1] + 30)  # Adjust the vertical spacing

    return img_with_strip


if __name__ == "__main__":
    app = ColorPickerApp()
    app.root.mainloop()
    result = app.get_value_logger()
    del app
    # image = choose_image()
    input_pdf = select_pdf()
    if not input_pdf:
        print('No PDF selected')
        exit()

    pdf_document = fitz.open(input_pdf)
    selected = False
    page_number=0
    while not selected:
        page = pdf_document.load_page(page_number)
        image_list = page.get_pixmap(matrix = fitz.Matrix(300/72, 300/72))
        image = Image.frombytes("RGB", [image_list.width, image_list.height], image_list.samples)
        image_np = np.array(image)
        image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        image_r = resize_image(image)
        image_x = show_instruction(image_r)
        image_x = image_x.astype(np.uint8)
        
        cv2.imshow("Select Image for Testing Range", image_x)

        key = cv2.waitKey(0) & 0xFF

        if key == 13:
            selected = True
            cv2.destroyAllWindows()
        elif key == 76 or key==108:
            page_number+=1
    
    if image is None:
        print("No image selected. Exiting.")
        exit()

    cv2.namedWindow('Trackbars')

    init_lower, init_upper = get_bounds(result) 

    create_trackbars()

    cv2.waitKey(0)
    get_final_values()
    cv2.destroyAllWindows()
