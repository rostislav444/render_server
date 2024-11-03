import os

replace = True
local = False

domain = 'http://0.0.0.0:8000' if local else 'http://194.15.46.132:8000'

root = os.path.dirname(os.path.abspath(__file__))
media_path = os.path.join(root, 'media')