from queue import Queue

class SongQueue:
  def __init__(self):
    self.__queue: Queue[tuple[str, str, str]] = Queue()
    self.current_song: tuple[str, str, str] = ( '', '' , '' )

  def add(self, url: str, title: str):
    self.__queue.put(( url, title, title.replace(' ', '_') ))

  def empty(self):
    return self.__queue.empty()

  def next(self):
    return self.__queue.get()

  def clear(self):
    self.__queue = Queue()