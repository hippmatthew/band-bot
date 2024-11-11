from typing import Optional
import discord

class Song:
  def __init__(self, title: str, url: str, requester: discord.Member, stream: str, length: str):
    self.title = title
    self.url = url
    self.requester = requester
    self.stream = stream
    self.length = length

class SongQueue:
  def __init__(self):
    self.__queue: list[Song] = []
    self.current_song: Optional[Song] = None

  def add(self, song: Song):
    self.__queue.append(song)

  def empty(self):
    return len(self.__queue) == 0

  def next(self):
    return self.__queue.pop(0)

  def clear(self):
    self.__queue = []

  def print(self) -> str:
    queue_str = ''
    for i, song in enumerate(self.__queue):
      if (i != 0):
        queue_str += '\n'
      queue_str += f'{i+1}: {song.title}'

    return queue_str