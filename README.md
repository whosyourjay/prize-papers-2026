# Prize Papers 2026

Edit `talks.toml` to change speakers, dates, titles, rooms, times, or reading
links. Then regenerate the static GitHub Pages site:

```sh
python3 generate.py
```

`index.html` is generated from `template.html` and `talks.toml`; do not edit it
directly. Python 3.11 or newer is required. To verify that the generated page is
current without changing it, run:

```sh
python3 generate.py --check
```
