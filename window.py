import tkinter as tk
from tkinter import messagebox
from process import VGMDownloader

class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VGM Downloader")
        self.geometry("600x240")
        self.resizable(False, False)
        self.url = tk.StringVar()
        self.download_info = tk.StringVar()
        self.download_info.set("※Takes time when retrieving album information")

    def button(self):
        def send_request():
            if self.url.get() and self.url.get().startswith("https://downloads.khinsider.com/"):
                self.vgm_downloader = VGMDownloader(self.url.get())
                soup = self.vgm_downloader.get_album_page()
                self.title, self.album_image = self.vgm_downloader.get_album_image(soup)
                dl_page = self.vgm_downloader.get_dl_page(soup)
                self.audio_format = self.vgm_downloader.get_audio_url(dl_page)
                if self.audio_format[0]: # MP3
                    self.mp3.config(state="normal")
                if self.audio_format[1]: # FLAC
                    self.flac.config(state="normal")
                if self.audio_format[2]: # OGG
                    self.ogg.config(state="normal")

                if self.mp3['state'] == self.flac['state'] == self.ogg['state'] == "disabled":
                    messagebox.showerror("Error", "No audio format available")
                    clear_entry()
            else:
                messagebox.showerror("Error", "Please enter a valid URL")
        
        def enable_download_btn():
            if selected_format:
                self.download_btn.config(state="normal")
                self.download_info.set("※It's totally fine when encountering the inevitable lag when downloading the album")
                self.download_label.place(x=15, y=210)
        
        def download_audio():
            audio_type = '1' if selected_format.get() == "mp3" else ('2' if selected_format.get() == "flac" else '3')
            self.vgm_downloader.download(audio_type, self.title, self.album_image, self.audio_format)

            messagebox.showinfo("info", "Download Complete")
            self.download_info.set("")
            clear_entry()

            self.mp3.config(state="disabled")
            self.flac.config(state="disabled")
            self.ogg.config(state="disabled")
            self.download_btn.config(state="disabled")

        def clear_entry():
            self.url.set("")
            self.url_entry.delete(0, tk.END)

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
                               command=clear_entry
                               )
        self.clear.place(x=448, y=60)
        # audio format button
        selected_format = tk.StringVar()
        formats_frame = tk.Frame(self)
        self.mp3 = tk.Radiobutton(formats_frame,
                                  text="MP3",
                                  font=("Arial", 14),
                                  variable=selected_format,
                                  value="mp3",
                                  state="disabled",
                                  command=enable_download_btn
                                  )
        self.flac = tk.Radiobutton(formats_frame,
                                  text="FLAC",
                                  font=("Arial", 14),
                                  variable=selected_format,
                                  value="flac",
                                  state="disabled",
                                  command=enable_download_btn
                                  )
        self.ogg = tk.Radiobutton(formats_frame,
                                  text="OGG",
                                  font=("Arial", 14),
                                  variable=selected_format,
                                  value="flac",
                                  state="disabled",
                                  command=enable_download_btn
                                  )
        self.mp3.pack(side="left")
        self.flac.pack(side="left")
        self.ogg.pack(side="left")
        formats_frame.pack(pady=100)
        # download button
        self.download_btn = tk.Button(self,
                                  text="Download",
                                  font=("Arial", 16),
                                  command=download_audio,
                                  state="disabled"
                                  )
        self.download_btn.place(x=250, y=150)

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
        self.download_label.place(x=125, y=210)
        