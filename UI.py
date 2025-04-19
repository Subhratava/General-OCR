import sys
import io
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QTextEdit, QFileDialog
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import pyautogui
from PIL import Image
import tkinter as tk
import win32clipboard 
import time
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from pathlib import Path

class SnipOCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snip + OCR Tool")
        self.setGeometry(100, 100, 800, 600)
        self.current_timer = None
        self.loader = False

        # Widgets
        self.snip_button = QPushButton("Snip")
        self.ocr_button = QPushButton("Run OCR")
        self.image_label = QLabel("Snipped image will appear here")
        self.ocr_result = QTextEdit("OCR text will appear here")
        self.ocr_result.setReadOnly(True)

        # Create a dropdown (QComboBox)
        self.combo = QComboBox()
        self.combo.addItems(["Timer : default", "Timer : 1s", "Timer : 2s", "Timer : 5s"])
        self.combo.currentIndexChanged.connect(self.snip_delay_timer)

        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.snip_button)
        layout.addWidget(self.ocr_button)
        layout.addWidget(self.combo)
        layout.addWidget(self.image_label)
        layout.addWidget(self.ocr_result)
        self.setLayout(layout)

        # Connections
        self.snip_button.clicked.connect(self.snip_screen)
        self.ocr_button.clicked.connect(self.run_ocr)
        self.combo.currentIndexChanged.connect(self.snip_delay_timer)

        self.snipped_image_path = None

    def snip_screen(self):
        # Tkinter screen selection
        coords = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
        rect_id = None
        self.showMinimized()
        time.sleep(0.2)

        if self.current_timer == "Timer : 1s":
            time.sleep(1)
        elif self.current_timer == "Timer : 2s":
            time.sleep(2)
        elif self.current_timer == "Timer : 5s":
            time.sleep(5)
        else:
            pass

        def on_mouse_down(event):
            coords["x1"], coords["y1"] = event.x, event.y
            nonlocal rect_id
            rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

        def on_mouse_move(event):
            if rect_id:
                canvas.coords(rect_id, coords["x1"], coords["y1"], event.x, event.y)

        def on_mouse_up(event):
            coords["x2"], coords["y2"] = event.x, event.y
            root.destroy()

        root = tk.Tk()
        root.attributes("-alpha", 0.3)
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        canvas = tk.Canvas(root, cursor="cross", bg="gray")
        canvas.pack(fill=tk.BOTH, expand=True)

        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

        root.mainloop()

        x1, y1 = coords["x1"], coords["y1"]
        x2, y2 = coords["x2"], coords["y2"]
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        width, height = x2 - x1, y2 - y1

        if width <= 0 or height <= 0:
            self.ocr_result.setText("⚠️ Invalid snip dimensions.")
            self.showNormal()
            self.raise_()
            QApplication.processEvents()
            return

        img = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))

        # self.snipped_image_path = "snipped_temp.png"
        # img.save(self.snipped_image_path)
        # Save using absolute path
        save_dir = Path(__file__).resolve().parent  # Same folder as script
        save_path = save_dir / "snipped_temp.png"
        img.save(str(save_path))

        self.snipped_image_path = str(save_path)

        # Show in QLabel
        self.display_image(self.snipped_image_path)

        # Save in clipboard
        self.image_to_clipboard(img)

        # Step 3: Restore the main app window
        self.showNormal()
        self.raise_()
        QApplication.processEvents()

    def display_image(self, path):
        image = QImage(path)
        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio))

    def run_ocr(self):
        #print(self.loader)
        if not self.snipped_image_path:
            self.ocr_result.setText("⚠️ No image to OCR. Please snip first.")
            return
        if not self.loader:
            self.load_model()
            self.loader = True
        
        image = self.snipped_image_path
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        
        generate_ids = self.model.generate(
            **inputs,
            do_sample=False,
            tokenizer=self.processor.tokenizer,
            stop_strings="<|im_end|>",
            max_new_tokens=4096,
        )
        
        text = self.processor.decode(generate_ids[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        #print(text)
        self.ocr_result.setText(text)

    def image_to_clipboard(self,img: Image.Image):
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Skip BMP header
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

    def snip_delay_timer(self,index):
        self.current_timer = self.combo.itemText(index)

    def load_model(self):
        import torch
        from transformers import AutoProcessor, AutoModelForImageTextToText
        save_dir = Path(__file__).resolve().parent  # Same folder as script
        model_path = str(save_dir / "got_ocr_model")
        #print(torch.cuda.is_available())
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # model = AutoModelForImageTextToText.from_pretrained("stepfun-ai/GOT-OCR-2.0-hf", device_map=device)
        # processor = AutoProcessor.from_pretrained("stepfun-ai/GOT-OCR-2.0-hf")
        self.model = AutoModelForImageTextToText.from_pretrained(model_path, device_map=self.device)
        self.processor = AutoProcessor.from_pretrained(model_path)
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SnipOCRApp()
    window.show()
    sys.exit(app.exec())
