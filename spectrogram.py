import tkinter as tk
import os
import requests
from dotenv import load_dotenv
from lxml import html
from bs4 import BeautifulSoup
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO
from requests.exceptions import MissingSchema

class Spectrogram(tk.Toplevel):
    def __init__(self, parent, window_title, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.geometry("761x613")
        self.resizable(False, False)
        self.title(window_title)
        self.parent = parent
        self.session = self.get_session()

        self.frame = tk.Frame(self,
                              width=744)
        self.frame.propagate(False)
        self.frame.pack(fill="both", expand=True)
        self.canvas_area()

        self.withdraw()

        self.protocol('WM_DELETE_WINDOW', self.callback)

    def callback(self):
        if not os.path.isfile("temp.png"):
            self.img_backup.save("temp.png")
        self.wm_state("withdrawn")

    def get_session(self):
        load_dotenv()
        login_url = 'https://downloads.khinsider.com/forums/index.php?login/login'
        s = requests.Session()
        result = s.get(login_url)
        tree = html.fromstring(result.text)
        token = list(set(tree.xpath('//input[@name="_xfToken"]/@value')))[0]
        payload = {
            'login' : os.getenv('EMAIL'),
            'password' : os.getenv('PASSWD'),
            '_xfToken' : token,
            '_xfRedirect': 'https://downloads.khinsider.com/forums/'
        }
        result = s.post(login_url, data=payload)
        return s

    def get_spectrogram(self):
        if hasattr(self.parent, 'url') and self.parent.url.get():
            if not self.parent.mp3['state'] == self.parent.flac['state'] == self.parent.ogg['state'] == 'disabled:':

                result = self.session.get(f'{self.parent.url.get()}/spectrograms')
                
                soup = BeautifulSoup(result.text, 'lxml')
                imgs = []
                for p in soup.find_all('p'):
                    img = p.find('img')
                    if img:
                        imgs.append(img['src'])
            return imgs

    def canvas_area(self):

        self.canvas = tk.Canvas(self.frame,
                                width=744,
                                height=613,
                                )
        self.scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack()

    def main(self):
        self.deiconify()
        self.canvas.delete("all")
        is_done = False
        while not is_done:
            try:
                if not os.path.isfile("temp.png"):
                    self.spectrogram_img = self.get_spectrogram()
                    new_canvas_height = len(self.spectrogram_img) * 615
                    self.canvas.config(scrollregion=(0, 0, 0, new_canvas_height))

                    self.img_backup = Image.new("RGB", (744, new_canvas_height))

                    self.images = []
                    for i, img in enumerate(self.spectrogram_img):
                        print(img)
                        if img.startswith("https://vgmtreasurechest.com"):
                            res = requests.get(img)
                            img = Image.open(BytesIO(res.content))
                            tk_img = ImageTk.PhotoImage(img)
                            self.images.extend([tk_img])
                            self.canvas.create_image(0, i * 615, anchor="nw", image=tk_img)
                            self.img_backup.paste(img, (0, i * 615))
                else:
                    self.backup = []
                    img = Image.open("temp.png")
                    new_canvas_height = img.height
                    self.canvas.config(scrollregion=(0, 0, 0, new_canvas_height))
                    tk_img = ImageTk.PhotoImage(img)
                    self.backup.extend([tk_img])
                    self.canvas.create_image(0, 0, anchor="nw", image=tk_img)
            except MissingSchema:
                continue
            finally:
                is_done = True


if __name__ == '__main__':
    root = tk.Tk()
    spectrogram = Spectrogram(root, "Spectrogram")
    spectrogram.main()
    root.mainloop()