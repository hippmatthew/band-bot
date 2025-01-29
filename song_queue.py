import discord
from threading import Thread
from typing import Optional, cast
from yt_dlp import YoutubeDL

class Song:
  def __init__(self, title: str, url: str, requester: discord.Member, length: str):
    self.title = title
    self.url = url
    self.requester = requester
    self.length = length
    self.stream = ""
    self._thread = Thread(target = self._download)

  def start_download(self):
    self._thread.start()

  def wait_for_stream(self):
    self._thread.join()

  def _download(self):
    if self.stream != "": return

    info = YoutubeDL({ "format": "bestaudio/best" }).extract_info( self.url, download = False )
    if not info:
      print(f"failed to download {self.title}")
      return
    self.stream = cast(str, info["url"])

class SongQueue:
  def __init__(self):
    self.__queue: list[Song] = []
    self.current_song: Optional[Song] = None

  def add(self, song: Song):
    self.__queue.append(song)

  def empty(self):
    return len(self.__queue) == 0

  def next(self):
    return self.__queue.pop(0) if not self.empty() else None

  def clear(self):
    self.__queue = []

  def print(self) -> str:
    queue_str = ''
    for i, song in enumerate(self.__queue):
      if (i != 0):
        queue_str += '\n'
      queue_str += f'{i+1}: {song.title}'

    return queue_str