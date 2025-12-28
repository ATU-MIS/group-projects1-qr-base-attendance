import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode as zbar_decode

PREVIEW_MAX_W = 295
PREVIEW_MAX_H = 265
WINDOW_W = 1080
WINDOW_H = 700
DEFAULT_FONT = ("Segoe UI", 12)
BUTTON_FONT = ("Segoe UI", 11)
LABEL_FONT = ("Segoe UI", 12, "bold")

class QRApp:
    def __init__(self, root):
        self.root = root
        root.title("Text ↔ QR (GUI)")
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.resizable(False, False)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass
        style.configure("TButton", font=BUTTON_FONT, padding=8)
        style.configure("TLabel", font=DEFAULT_FONT)
        style.configure("TCombobox", font=DEFAULT_FONT, padding=4)
        style.configure("TSpinbox", font=DEFAULT_FONT)
        self.frame = ttk.Frame(root, padding=12)
        self.frame.grid(sticky="nsew")
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=0)
        self.input_label = ttk.Label(self.frame, text="Text to encode:", font=LABEL_FONT)
        self.input_label.grid(row=0, column=0, sticky="w")
        self.input_text = ScrolledText(self.frame, width=72, height=12, font=DEFAULT_FONT, wrap="word")
        self.input_text.grid(row=1, column=0, sticky="nsew", pady=(6,10))
        self.controls_frame = ttk.Frame(self.frame)
        self.controls_frame.grid(row=2, column=0, sticky="w", pady=(4,8))
        ttk.Label(self.controls_frame, text="Error correction:", font=DEFAULT_FONT).grid(row=0, column=0, padx=(0,8), sticky="w")
        self.error_var = tk.StringVar(value="M (15%)")
        self.error_combo = ttk.Combobox(self.controls_frame, textvariable=self.error_var, state="readonly", width=14)
        self.error_combo['values'] = ("L (7%)","M (15%)","Q (25%)","H (30%)")
        self.error_combo.grid(row=0, column=1, padx=(0,14))
        ttk.Label(self.controls_frame, text="Box size:", font=DEFAULT_FONT).grid(row=0, column=2, padx=(0,8))
        self.box_var = tk.IntVar(value=10)
        self.box_spin = ttk.Spinbox(self.controls_frame, from_=1, to=40, textvariable=self.box_var, width=6)
        self.box_spin.grid(row=0, column=3, padx=(0,14))
        ttk.Label(self.controls_frame, text="Border:", font=DEFAULT_FONT).grid(row=0, column=4, padx=(0,8))
        self.border_var = tk.IntVar(value=4)
        self.border_spin = ttk.Spinbox(self.controls_frame, from_=0, to=20, textvariable=self.border_var, width=6)
        self.border_spin.grid(row=0, column=5, padx=(0,8))
        self.buttons_frame = ttk.Frame(self.frame)
        self.buttons_frame.grid(row=3, column=0, sticky="w", pady=(12,12))
        self.generate_btn = ttk.Button(self.buttons_frame, text="Generate QR", command=self.generate_qr)
        self.generate_btn.grid(row=0, column=0, padx=6)
        self.generate_btn.config(width=16)
        self.save_btn = ttk.Button(self.buttons_frame, text="Save QR", command=self.save_qr)
        self.save_btn.grid(row=0, column=1, padx=6)
        self.save_btn.config(width=12)
        self.clear_btn = ttk.Button(self.buttons_frame, text="Clear", command=self.clear_all)
        self.clear_btn.grid(row=0, column=2, padx=6)
        self.clear_btn.config(width=12)
        self.open_btn = ttk.Button(self.buttons_frame, text="Open QR Image", command=self.open_qr_image)
        self.open_btn.grid(row=0, column=3, padx=6)
        self.open_btn.config(width=16)
        self.copy_btn = ttk.Button(self.buttons_frame, text="Copy Decoded", command=self.copy_decoded)
        self.copy_btn.grid(row=0, column=4, padx=6)
        self.copy_btn.config(width=14)

        self.preview_frame = ttk.Frame(self.frame, relief="flat", width=PREVIEW_MAX_W + 28, height=(PREVIEW_MAX_H * 2) + 96)
        self.preview_frame.grid(row=0, column=1, rowspan=20, padx=(18,20), sticky="ne")
        self.preview_frame.grid_propagate(False)

        self.upload_label_title = ttk.Label(self.preview_frame, text="Uploaded Image", font=LABEL_FONT)
        self.upload_label_title.place(x=12, y=0)
        self.preview_image_canvas = tk.Label(self.preview_frame, background="white", bd=1, relief="solid")
        self.preview_image_canvas.place(x=12, y=36, width=PREVIEW_MAX_W, height=PREVIEW_MAX_H)
        self.qr_label_title = ttk.Label(self.preview_frame, text="Generated QR", font=LABEL_FONT)
        self.qr_label_title.place(x=12, y=36 + PREVIEW_MAX_H + 12)
        self.preview_qr_canvas = tk.Label(self.preview_frame, background="white", bd=1, relief="solid")
        self.preview_qr_canvas.place(x=12, y=36 + PREVIEW_MAX_H + 44, width=PREVIEW_MAX_W, height=PREVIEW_MAX_H)

        ttk.Label(self.frame, text="Decoded / Current text:", font=LABEL_FONT).grid(row=4, column=0, sticky="w")
        self.decoded_text = ScrolledText(self.frame, width=72, height=8, font=DEFAULT_FONT, wrap="word")
        self.decoded_text.grid(row=5, column=0, sticky="nsew", pady=(8,10))
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var, anchor="w", font=DEFAULT_FONT)
        self.status_label.grid(row=6, column=0, columnspan=2, sticky="we", pady=(4,2))
        self.qr_image = None
        self.preview_qr_photo = None
        self.uploaded_image = None
        self.upload_photo = None
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.save_btn.state(["disabled"])
        self.copy_btn.state(["disabled"])

    def map_error(self, text):
        return {"L (7%)": ERROR_CORRECT_L, "M (15%)": ERROR_CORRECT_M, "Q (25%)": ERROR_CORRECT_Q, "H (30%)": ERROR_CORRECT_H}.get(text, ERROR_CORRECT_M)

    def generate_qr(self):
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Info", "Please enter text to encode.")
            return
        ec = self.map_error(self.error_var.get())
        box = max(1, int(self.box_var.get()))
        border = max(0, int(self.border_var.get()))
        qr = qrcode.QRCode(error_correction=ec, box_size=box, border=border)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        self.qr_image = img
        self.show_qr_preview(img)
        self.status_var.set("QR generated")
        self.save_btn.state(["!disabled"])

    def show_qr_preview(self, pil_img):
        w, h = pil_img.size
        scale = min(PREVIEW_MAX_W / w, PREVIEW_MAX_H / h, 1.0)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (PREVIEW_MAX_W, PREVIEW_MAX_H), (255,255,255))
        x = (PREVIEW_MAX_W - new_w) // 2
        y = (PREVIEW_MAX_H - new_h) // 2
        canvas.paste(img, (x, y))
        self.preview_qr_photo = ImageTk.PhotoImage(canvas)
        self.preview_qr_canvas.configure(image=self.preview_qr_photo)

    def show_uploaded_image(self, pil_img):
        w, h = pil_img.size
        scale = min(PREVIEW_MAX_W / w, PREVIEW_MAX_H / h, 1.0)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (PREVIEW_MAX_W, PREVIEW_MAX_H), (255,255,255))
        x = (PREVIEW_MAX_W - new_w) // 2
        y = (PREVIEW_MAX_H - new_h) // 2
        canvas.paste(img, (x, y))
        self.upload_photo = ImageTk.PhotoImage(canvas)
        self.preview_image_canvas.configure(image=self.upload_photo)

    def save_qr(self):
        if self.qr_image is None:
            messagebox.showinfo("Info", "No QR image to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image","*.png"),("All files","*.*")])
        if not path:
            return
        try:
            self.qr_image.save(path)
            self.status_var.set(f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

    def clear_all(self):
        self.input_text.delete("1.0", "end")
        self.decoded_text.delete("1.0", "end")
        self.preview_qr_canvas.configure(image="")
        self.preview_image_canvas.configure(image="")
        self.qr_image = None
        self.preview_qr_photo = None
        self.uploaded_image = None
        self.upload_photo = None
        self.save_btn.state(["disabled"])
        self.copy_btn.state(["disabled"])
        self.status_var.set("Cleared")

    def open_qr_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files","*.png;*.jpg;*.jpeg;*.bmp;*.gif"),("All files","*.*")])
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image: {e}")
            return
        self.uploaded_image = img
        self.show_uploaded_image(img)
        decoded = self.decode_pil(img)
        if decoded:
            self.decoded_text.delete("1.0", "end")
            self.decoded_text.insert("1.0", decoded)
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", decoded)
            self.copy_btn.state(["!disabled"])
            self.status_var.set("Decoded and copied into input for editing")
        else:
            self.status_var.set("No QR code found in uploaded image")
        self.save_btn.state(["!disabled"])

    def decode_pil(self, pil_img):
        try:
            data = zbar_decode(pil_img)
            if not data:
                return ""
            texts = [d.data.decode("utf-8", errors="replace") for d in data]
            return "\n".join(texts)
        except Exception:
            return ""

    def copy_decoded(self):
        txt = self.decoded_text.get("1.0", "end").strip()
        if not txt:
            messagebox.showinfo("Info", "No decoded text to copy.")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            self.status_var.set("Copied decoded text to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy to clipboard: {e}")

    def on_close(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = QRApp(root)
    root.mainloop()
