import os

replace = True
local = True

domain = 'http://0.0.0.0:8000' if local else 'http://194.15.46.132:8000'

root = os.path.dirname(os.path.abspath(__file__))
media_path = os.path.join(root, 'media')


filter_parts = []
manual_ids = []

write_anyway = input('Write anyway? (y/n): ').lower() == 'y'
make_render = input('Render? (y/n): ').lower() == 'y'
ids = manual_ids if len(manual_ids) > 0 else [int(i) for i in input('Enter ids: ').replace(' ', '').split(',')]
hdr = True
