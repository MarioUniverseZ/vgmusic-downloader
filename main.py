import os
import re
import requests as req
from time import time, sleep
from requests.exceptions import RequestException
from bs4 import BeautifulSoup as bs
from urllib.parse import unquote
import threading
from queue import Queue

def get_audio_choice():
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
        if mp3:
            print("\nNo input received, defaulting to MP3" + "\n")
            return '1'
        elif flac:
            print("\nNo input received, defaulting to FLAC" + "\n")
            return '2'
        elif ogg:
            print("\nNo input received, defaulting to OGG" + "\n")
            return '3'
    return queue.get()

def get_filename(url_filename: str):
    """
    get filename from url
    """
    return unquote(url_filename.split("/")[-1])

def list_remove_duplicate(lst: list):
    """
    remove duplicate elements in a list
    """
    return list(dict.fromkeys(lst))

def get_album_image(soup: bs):
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

            album_image = list_remove_duplicate(album_image)
            print("audio images retrieved" + "\n") if album_image else print("no audio image found")
            return title, album_image if title and album_image else None
        except RequestException:
            sleep(5)
            continue

def get_dl_page(soup: bs):
    """
    get every single download page from album song list
    """
    while True:
        try:
            print("getting download pages...")
            text = soup.find_all("td", class_="clickable-row")
            dl_page = []

            if res.status_code == 200:
                for element in text:
                    dl_page.append(f'https://downloads.khinsider.com{element.find("a")["href"]}')

            dl_page = list_remove_duplicate(dl_page)
            print("all download pages retrieved" + "\n")
            return dl_page
        except RequestException:
            sleep(5)
            continue

def get_audio_url(page_list: list):
    """
    get audio url from a list of download page
    """
    while True:
        try:
            print("getting audio urls...(this may take a while)")
            mp3 = []
            flac = []
            ogg = []
            
            for pages in dl_page:
                res = req.get(pages)
                if res.status_code == 200:
                    soup = bs(res.text, 'lxml')
                    for link in soup.find_all('a'):
                        if link.get('href').endswith('.mp3'):
                            mp3.append(link.get('href'))
                        elif link.get('href').endswith('.flac'):
                            flac.append(link.get('href'))
                        elif link.get('href').endswith('.ogg'):
                            ogg.append(link.get('href'))

            mp3 = list_remove_duplicate(mp3)
            flac = list_remove_duplicate(flac)
            ogg = list_remove_duplicate(ogg)

            print(f"all audio urls retrieved. mp3:{"available" if bool(mp3) else "unavailable"}, flac:{"available" if bool(flac) else "unavailable"}, ogg:{"available" if bool(ogg) else "unavailable"}")

            return mp3, flac, ogg
        except RequestException:
            sleep(5)
            continue

def download(decision: str, album_name: str):
    """
    download audio
    """
    if not os.path.isdir(album_name):
        os.mkdir(album_name)
    if not os.path.isdir(title + "/albumImage"):
        os.mkdir(title + "/albumImage")

    while True:
        target_format = mp3 if decision == '1' else (flac if decision == '2' else ogg)
        try:
            if decision == '1' and not mp3:
                print("no mp3 audio found, choosing flac audio instead")
                target_format = flac
            elif  decision == '2' and not flac:
                print("no flac audio found, choosing mp3 audio instead")
                target_format = mp3

            print("downloading...(this may take a while)")

            # download album image
            if album_image:
                for element in album_image:
                    res = req.get(element)
                    if res.status_code == 200:
                        filename = get_filename(element)
                        with open(title + "/albumImage/" + filename, 'wb') as f:
                            f.write(res.content)
                        print(f"{title}/albumImage/{filename} downloaded")

            # download audio
            for element in target_format:
                res = req.get(element)
                if res.status_code == 200:
                    filename = get_filename(element)
                    with open(f"{title}/{filename}", "wb") as o:
                        o.write(res.content)
                    print(f"{title}/{filename} downloaded")
        
            return

        except RequestException:
            sleep(5)
            continue

if __name__ == '__main__':
    url = input('Enter URL: ')
    start = time()
    res = req.get(url)

    if res.status_code == 200:
        soup = bs(res.text, 'lxml')

        title, album_image = get_album_image(soup)
        dl_page = get_dl_page(soup)
        mp3, flac, ogg = get_audio_url(dl_page)

        if bool(mp3) == False and bool(flac) == False and bool(ogg) == False:
            print("No audio found")
            exit()

        print(f"retrieved every single audio urls in {time() - start:.2f}s" + "\n")

        audio_type = get_audio_choice()
        download(audio_type, title)

        print(f"Finished downloading. Total time: {time() - start:.2f}s")