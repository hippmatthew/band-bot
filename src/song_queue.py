from discord import Member
from threading import Thread
from typing import cast, Optional
from yt_dlp import YoutubeDL

class Song:
  title: str
  url: str
  requester: Member
  length: str
  __thread: Thread

  def __init__(self, title: str, url: str, requester: Member, length: str) -> None:
    self.title = title
    self.url = url
    self.requester = requester
    self.length = length
    self.stream = ''
    self.__thread = Thread(target = self.__download)

  def start_download(self) -> None:
    self.__thread.start()

  def wait_for_stream(self) -> None:
    self.__thread.join()

  def __download(self) -> None:
    if self.stream != '': return

    info = YoutubeDL({ 'format': 'bestaudio/best' }).extract_info( self.url, download = False )
    if not info:
      print(f'failed to download {self.title}')
      return
    self.stream = cast(str, info['url'])

class SongQueue:
  current_song: Optional[Song]
  __queue: list[Song]

  def __init__(self) -> None:
    self.current_song = None
    self.__queue = []

  def __str__(self) -> str:
    queue_str: str = ''
    for i, song in enumerate(self.__queue):
      if (i != 0):
        queue_str += '\n'
      queue_str += f'{i + 1}: {song.title}'
    return queue_str

  def add(self, song: Song) -> None:
    self.__queue.append(song)

  def empty(self) -> bool:
    return len(self.__queue) == 0

  def next(self) -> Optional[Song]:
    return self.__queue.pop(0) if not self.empty() else None

  def clear(self) -> None:
    self.__queue = []