import os
import re
import requests as req
from time import time, sleep
from requests.exceptions import RequestException
from bs4 import BeautifulSoup as bs
from urllib.parse import unquote
import threading
import concurrent
from queue import Queue
# from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from requests.models import Response

class VGMDownloader():
    def __init__(self, url: str):
        self.url = url
        self.executor = ThreadPoolExecutor(max_workers=20)

    def get_album_page(self):
        """
        return a soup object or exit automatically if the page is not available
        """

        try:
            res_album_page = req.get(self.url)
            soup = bs(res_album_page.text, 'lxml')
            return soup
        except RequestException:
            print("page temporarily unavailable")
    
    def get_album_image(self, soup: bs):
        """
        get images from an album
        """
        while True:
            try:
                print("getting album title...")
                text = soup.find_all("div", class_="albumImage")
                title = re.sub(r'[\\/*?:"<>|]', "", soup.find("h2").get_text()) #remove invalid characters ans pass this to create folder later on
                print(f"album title: {title}" + "\n")
                album_image = []

                print("getting album image...")

                for element in text: #div.a.img
                    album_image.append(unquote(element.find("a")['href']))

                album_image = self.list_remove_duplicate(album_image)
                print("audio images retrieved" + "\n") if album_image else print("no audio image found")
                return title, album_image if title and album_image else None
            except RequestException:
                sleep(5)
                continue

    def get_dl_page(self, soup: bs):
        """
        get every single download page from album song list
        """
        while True:
            try:
                print("getting download pages...")
                text = soup.find_all("td", class_="clickable-row")
                dl_page = []

                for element in text:
                    dl_page.append(f'https://downloads.khinsider.com{element.find("a")["href"]}')

                dl_page = self.list_remove_duplicate(dl_page)
                print("all download pages retrieved" + "\n")
                return dl_page
            except RequestException:
                sleep(5)
                continue

    def get_audio_url(self, dl_page: list):
        """
        get audio url from a list of download page
        """
        while True:
            try:
                print("getting audio urls...(this may take a while)")
                mp3 = []
                flac = []
                ogg = []
                
                res = [self.executor.submit(req.get, pages) for pages in dl_page]
                concurrent.futures.wait(res)
                response = [r.result() for r in res]
                soup = [bs(r.text, 'lxml') for r in response]

                for soup in soup:
                    for link in soup.find_all('a'):
                        if link.get('href').endswith('.mp3'):
                            mp3.append(link.get('href'))
                        elif link.get('href').endswith('.flac'):
                            flac.append(link.get('href'))
                        elif link.get('href').endswith('.ogg'):
                            ogg.append(link.get('href'))

                mp3 = self.list_remove_duplicate(mp3)
                flac = self.list_remove_duplicate(flac)
                ogg = self.list_remove_duplicate(ogg)

                print(f"all audio urls retrieved. mp3:{"available" if bool(mp3) else "unavailable"}, flac:{"available" if bool(flac) else "unavailable"}, ogg:{"available" if bool(ogg) else "unavailable"}")

                return mp3, flac, ogg
            except RequestException:
                sleep(5)
                continue

    def get_audio_choice(self, audio_format: tuple):
        def input_thread(queue):
            valid_types = {'1', '2', '3'}
            while True:
                audio_type = input("Enter the audio type (1=mp3, 2=flac or 3=ogg): ").strip()
                if audio_type in valid_types:
                    queue.put(audio_type)
                    break
                print("Invalid input, try again")

        queue = Queue()
        thread = threading.Thread(target=input_thread, args=(queue,))
        thread.daemon = True
        thread.start()
        thread.join(timeout=10)  # Wait 10 seconds for input

        if queue.empty():
            if audio_format[0]:
                print("\nNo input received, defaulting to MP3" + "\n")
                return '1'
            elif audio_format[1]:
                print("\nNo input received, defaulting to FLAC" + "\n")
                return '2'
            elif audio_format[2]:
                print("\nNo input received, defaulting to OGG" + "\n")
                return '3'
        return queue.get()

    def get_filename(self, url_filename: str):
        """
        get filename from url
        """
        return unquote(url_filename.split("/")[-1])

    def list_remove_duplicate(self, lst: list):
        """
        remove duplicate elements in a list
        """
        return list(dict.fromkeys(lst))

    def parallel_download(self, res: Response, title: str, filename: str, *album_image):
        try:
            if album_image:
                with open(f"{title}/albumImage/{filename}", "wb") as f:
                    f.write(res.content)
                    print(f"album image downloaded to {title}/albumImage/{filename}")
            else:
                with open(f"{title}/{filename}", "wb") as f:
                    f.write(res.content)
                    print(f"audio downloaded to {title}/{filename}")
        except ConnectionResetError:
            print("Connection reset by peer")
            exit()


    def download(self, decision: str, title: str, album_image: list, audio_format: tuple):
        """
        download audio
        """

        if not os.path.isdir(title):
            os.mkdir(title)
        if not os.path.isdir(title + "/albumImage"):
            os.mkdir(title + "/albumImage")

        while True:
            target_format = audio_format[0] if decision == '1' else (audio_format[1] if decision == '2' else audio_format[2])
            try:
                if decision == '1' and not audio_format[0]:
                    print("no mp3 audio found, choosing flac audio instead")
                    target_format = audio_format[1]
                elif  decision == '2' and not audio_format[1]:
                    print("no flac audio found, choosing mp3 audio instead")
                    target_format = audio_format[0]

                print("downloading...(this may take a while)")

                # download album image
                if album_image:
                    res = [self.executor.submit(req.get, element) for element in album_image]
                    concurrent.futures.wait(res)
                    filename = [self.get_filename(element) for element in album_image]
                    dow = [self.executor.submit(self.parallel_download, res[index].result(), title, filename[index], album_image) for index in range(len(album_image))]
                    concurrent.futures.wait(dow)
                    sleep(2)

                # download audio
                if target_format:
                    res = [self.executor.submit(req.get, element) for element in target_format]
                    concurrent.futures.wait(res)
                    filename = [self.get_filename(element) for element in target_format]
                    dow = [self.executor.submit(self.parallel_download, res[index].result(), title, filename[index]) for index in range(len(target_format))]
                    concurrent.futures.wait(dow)
                    sleep(2)
                else:
                    raise("This audio format is not available! Maybe you selected the wrong one")
                
                return

            except RequestException:
                sleep(5)
                continue

if __name__ == '__main__':
    url = input('Enter URL: ')
    start = time()
    res = VGMDownloader(url)
    soup = res.get_album_page()

    title, album_image = res.get_album_image(soup)
    dl_page = res.get_dl_page(soup)
    audio_format = res.get_audio_url(dl_page)

    print(f"retrieved every single audio urls in {time() - start:.2f}s" + "\n")

    audio_type = res.get_audio_choice()
    res.download(audio_type, title, album_image, audio_format)

    print(f"Finished downloading. Total time: {time() - start:.2f}s")