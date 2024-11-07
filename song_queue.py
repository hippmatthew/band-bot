class SongQueue:
  def __init__(self):
    self.urls = []

  def add(self, url):
    self.urls.append(url)

  def remove(self, url):
    self.urls.remove(url)

  def empty(self):
    return len(self.urls) == 0

  def next(self):
    return self.urls.pop(0)

  def clear(self):
    self.urls = []