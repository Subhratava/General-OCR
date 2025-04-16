import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import requests
from io import BytesIO

print(torch.cuda.is_available())
device = "cuda" if torch.cuda.is_available() else "cpu"
# model = AutoModelForImageTextToText.from_pretrained("stepfun-ai/GOT-OCR-2.0-hf", device_map=device)
# processor = AutoProcessor.from_pretrained("stepfun-ai/GOT-OCR-2.0-hf")
model = AutoModelForImageTextToText.from_pretrained("got_ocr_model", device_map=device)
processor = AutoProcessor.from_pretrained("got_ocr_model")

def get_ocr(path):
    image = path
    inputs = processor(image, return_tensors="pt").to(device)
    
    generate_ids = model.generate(
        **inputs,
        do_sample=False,
        tokenizer=processor.tokenizer,
        stop_strings="<|im_end|>",
        max_new_tokens=4096,
    )
    
    return processor.decode(generate_ids[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)

import tkinter as tk
from PIL import ImageGrab, Image
import pyautogui
import io
import win32clipboard  # Windows only
from PIL import ImageTk
import time

coords = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
rect_id = None

def on_mouse_down(event):
    coords["x1"] = event.x
    coords["y1"] = event.y
    global rect_id
    rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

def on_mouse_move(event):
    if rect_id:
        canvas.coords(rect_id, coords["x1"], coords["y1"], event.x, event.y)

def on_mouse_up(event):
    coords["x2"] = event.x
    coords["y2"] = event.y
    root.destroy()

def image_to_clipboard(img: Image.Image):
    output = io.BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]  # Skip BMP header
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

# --- UI setup ---
time.sleep(0.5)
root = tk.Tk()
root.attributes("-alpha", 0.3)
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg='gray')

canvas = tk.Canvas(root, cursor="cross", bg='gray')
canvas.pack(fill=tk.BOTH, expand=True)

canvas.bind("<ButtonPress-1>", on_mouse_down)
canvas.bind("<B1-Motion>", on_mouse_move)
canvas.bind("<ButtonRelease-1>", on_mouse_up)

print("🔲 Drag to select screen area...")
root.mainloop()

# Get coordinates
x1, y1 = coords["x1"], coords["y1"]
x2, y2 = coords["x2"], coords["y2"]
x1, x2 = sorted([x1, x2])
y1, y2 = sorted([y1, y2])
width, height = x2 - x1, y2 - y1

# Screenshot selected area
screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
screenshot.save("snipped_area.png")
image_to_clipboard(screenshot)

print("✅ Snip saved as 'snipped_area.png'")
print("📋 Image copied to clipboard!")
print(get_ocr("snipped_area.png"))
