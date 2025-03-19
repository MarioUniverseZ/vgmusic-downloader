import tkinter as tk
from tkinter import messagebox
from process import VGMDownloader
from requests.exceptions import RequestException
import threading

class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VGM Downloader")
        self.geometry("600x270")
        self.iconbitmap("icon.ico")
        self.resizable(False, False)
        self.url = tk.StringVar()
        self.download_info = tk.StringVar()
        self.download_info.set("※Takes time when retrieving album information")

    def button(self):
        def send_request():
            # Disable the button during processing
            self.send_btn.config(state="disabled")
            
            # Create and start a thread for network operations
            thread = threading.Thread(target=self.process_request)
            thread.daemon = True
            thread.start()
        
        def enable_download_btn():
            if self.selected_format:
                self.download_btn.config(state="normal")
                self.clear.config(state="normal")
            if not self.selected_format.get():
                self.download_btn.config(state="disabled")
        
        def download_audio():
            if self.selected_format.get():
                thread = threading.Thread(target=self.process_download)
                thread.daemon = True
                thread.start()
            else:
                messagebox.showerror("Error", "Please select an audio format")

        # send request button
        self.send_btn = tk.Button(self,
                             text="Send Request",
                             font=("Arial", 16),
                             command=send_request
                             )
        self.send_btn.place(x=435, y=10)
        # clear entry
        self.clear = tk.Button(self,
                               text="Clear Entry",
                               font=("Arial", 16),
                               command=self.clear_entry
                               )
        self.clear.place(x=448, y=60)
        # audio format button
        self.selected_format = tk.StringVar()
        formats_frame = tk.Frame(self)
        self.mp3 = tk.Checkbutton(formats_frame,
                                  text="MP3",
                                  font=("Arial", 14),
                                  variable=self.selected_format,
                                  onvalue="mp3", offvalue="",
                                  state="disabled",
                                  command=enable_download_btn
                                  )
        self.flac = tk.Checkbutton(formats_frame,
                                  text="FLAC",
                                  font=("Arial", 14),
                                  variable=self.selected_format,
                                  onvalue="flac", offvalue="",
                                  state="disabled",
                                  command=enable_download_btn
                                  )
        self.ogg = tk.Checkbutton(formats_frame,
                                  text="OGG",
                                  font=("Arial", 14),
                                  variable=self.selected_format,
                                  onvalue="ogg", offvalue="",
                                  state="disabled",
                                  command=enable_download_btn
                                  )
        self.mp3.pack(side="left")
        self.flac.pack(side="left")
        self.ogg.pack(side="left")
        self.mp3.deselect()
        self.flac.deselect()
        self.ogg.deselect()
        formats_frame.pack(pady=100)
        # download button
        self.download_btn = tk.Button(self,
                                  text="Download",
                                  font=("Arial", 16),
                                  command=download_audio,
                                  state="disabled"
                                  )
        self.download_btn.place(x=250, y=150)

    def process_request(self):
        try:
            if self.url.get() and self.url.get().startswith("https://downloads.khinsider.com/"):
                self.vgm_downloader = VGMDownloader(self.url.get())

                self.disable_btn()
                
                # Update UI from main thread
                self.after(0, lambda: self.download_info.set("※Retrieving album information..."))
                soup = self.vgm_downloader.get_album_page()
                
                self.after(0, lambda: self.download_info.set("※Retrieving album image"))
                title, album_image = self.vgm_downloader.get_album_image(soup)
                
                self.after(0, lambda: self.download_info.set("※Retrieving download page"))
                dl_page = self.vgm_downloader.get_dl_page(soup)
                
                self.after(0, lambda: self.download_info.set("※Retrieving available audio formats"))
                audio_format = self.vgm_downloader.get_audio_url(dl_page)
                
                # Update UI elements from main thread
                self.after(0, lambda: self.update_ui(title, album_image, audio_format))
            else:
                self.after(0, lambda: messagebox.showerror("Error", "Please enter a valid URL"))
                self.after(0, lambda: self.send_btn.config(state="normal"))
        except RequestException:
            self.after(0, lambda: messagebox.showerror("Error", "page temporarily unavailable"))
            self.after(0, lambda: self.send_btn.config(state="normal"))
    
    def update_ui(self, title, album_image, audio_format):
        # Store the data
        self.title = title
        self.album_image = album_image
        self.audio_format = audio_format
        
        # Update UI based on available formats
        if self.audio_format[0]:  # MP3
            self.mp3.config(state="normal")
        if self.audio_format[1]:  # FLAC
            self.flac.config(state="normal")
        if self.audio_format[2]:  # OGG
            self.ogg.config(state="normal")
            
        self.download_info.set("※URLs retrieved")
        
        if self.mp3['state'] == self.flac['state'] == self.ogg['state'] == "disabled":
            messagebox.showerror("Error", "No audio format available")
            self.clear_entry()
            
        # Re-enable the send button
        self.send_btn.config(state="normal")

    def process_download(self):
        if self.selected_format.get():
            audio_type = '1' if self.selected_format.get() == "mp3" and self.mp3['state'] == "normal" else('2' if self.selected_format.get() == "flac" and self.flac['state'] == "normal" else '3')
            self.download_info.set("※Downloading...(this may take a while)")
            self.disable_btn()
            self.vgm_downloader.download(audio_type, self.title, self.album_image, *self.audio_format)

            messagebox.showinfo("info", "Download Complete")
            self.download_info.set("")
            self.clear_entry()
        else:
            messagebox.showerror("Error", "Please select an audio format")

    def entry(self):
        self.url_entry = tk.Entry(self,
                                  textvariable=self.url,
                                  font=("Arial", 16),
                                  width=33,
                                  justify="left"
                                  )
        self.url_entry.place(x=10, y=40)

    def label(self):
        self.download_label = tk.Label(self,
                                       textvariable=self.download_info,
                                       font=("Arial", 12),
                                       )
        self.download_label.pack(side="bottom")
        
    def clear_entry(self):
        self.url.set("")
        self.mp3.config(state="disabled")
        self.flac.config(state="disabled")
        self.ogg.config(state="disabled")
        self.mp3.deselect()
        self.flac.deselect()
        self.ogg.deselect()
        self.download_btn.config(state="disabled")
        self.clear.config(state="normal")
        self.send_btn.config(state="normal")
        self.url_entry.delete(0, tk.END)

    def disable_btn(self):
        self.send_btn.config(state="disabled")
        self.download_btn.config(state="disabled")
        self.clear.config(state="disabled")