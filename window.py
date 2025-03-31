import tkinter as tk
import os
from tkinter import messagebox
from process import VGMDownloader
from requests.exceptions import RequestException
from tkinter.filedialog import askdirectory
from configparser import ConfigParser
from spectrogram import Spectrogram
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
        self.spectrogram = Spectrogram(self, window_title="Spectrogram")

        self.config = ConfigParser()
        has_ini = self.config.read("config.ini")
        self.path = self.config.get("DEFAULT", "path") if has_ini else ""

        self.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        if os.path.isfile("temp.png"):
            os.remove("temp.png")
        self.quit()

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
                global target_dir
                if self.path:
                    target_dir = askdirectory(title="Select Directory", initialdir=self.path)
                else:
                    target_dir = askdirectory(title="Select Directory")
                if target_dir:
                    self.config['DEFAULT']['path'] = target_dir
                    with open('config.ini', 'w') as configfile:
                        self.config.write(configfile)
                    thread = threading.Thread(target=self.process_download)
                    thread.daemon = True
                    thread.start()
                else:
                    messagebox.showerror("Error", "Please select a directory")
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
        formats_frame.pack(pady=(110,0))
        # download button
        self.download_text = tk.StringVar()
        self.download_text.set("Download")
        self.download_btn = tk.Button(self,
                                  font=("Arial", 16),
                                  command=download_audio,
                                  textvariable=self.download_text,
                                  state="disabled"
                                  )
        self.download_btn.pack(pady=(10,0))

    def process_request(self):
        try:
            if self.url.get() and self.url.get().startswith("https://downloads.khinsider.com/"):
                if os.path.isfile("temp.png"):
                    os.remove("temp.png")
                self.vgm_downloader = VGMDownloader(self.url.get())

                self.spectrogram.wm_state("withdrawn")
                self.view_spectrogram.place_forget()
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
        self.url_entry.config(state="normal")
        self.clear.config(state="normal")
        
        if self.mp3['state'] == self.flac['state'] == self.ogg['state'] == "disabled":
            messagebox.showerror("Error", "No audio format available")
            self.clear_entry()
        else:
            # Re-enable the send button
            self.send_btn.config(state="normal")

            self.view_spectrogram.place(x=10, y=80)
            self.view_spectrogram.bind("<Button-1>", lambda e: self.open_spectrogram())

    def open_spectrogram(self):
        self.spectrogram.main()

    def process_download(self):
        if self.selected_format.get():
            audio_type = '1' if self.selected_format.get() == "mp3" and self.mp3['state'] == "normal" else('2' if self.selected_format.get() == "flac" and self.flac['state'] == "normal" else '3')
            self.download_info.set("※Downloading...(this may take a while)")
            self.disable_btn()
            self.title = f'{target_dir}\\{self.title}'
            self.download_text.set("Downloading...")
            self.vgm_downloader.download(audio_type, self.title, self.album_image, *self.audio_format)

            messagebox.showinfo("info", "Download Complete")
            self.download_info.set("")
            self.clear_entry()
            self.download_text.set("Download")
            self.url_entry.config(state="normal")
            self.view_spectrogram.place_forget()
            self.spectrogram.callback()

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

        self.view_spectrogram = tk.Label(self,
                                         text="View Spectrogram(New Window)",
                                         font=("Arial", 10),
                                         foreground="blue",
                                         underline=0
                                         )
        
    def clear_entry(self):
        self.url.set("")
        self.download_info.set("")
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
        self.view_spectrogram.place_forget()

    def disable_btn(self):
        self.send_btn.config(state="disabled")
        self.download_btn.config(state="disabled")
        self.clear.config(state="disabled")
        self.url_entry.config(state="disabled")
        self.mp3.config(state="disabled")
        self.flac.config(state="disabled")
        self.ogg.config(state="disabled")