# pybrp
Simple Python utility for BombSquad's replay files.

# Inline Usage
```Python
>>> import pybrp
>>> # initialize huffman
>>> _h = pybrp._H()
>>> # file in, file out
>>> fi: str = 'nice.brp'
>>> fo: str = 'nice.raw'
>>> # decompress into raw bytes
>>> pybrp.decompress(_h,fi,fo)
>>> # get duration in milleseconds
>>> ms: int = pybrp.get_duration(_h,fi)
>>> # get events by timestamp
>>> stamp: int = 123
>>> data: dict = pybrp.get_data(_h,fi)
>>> events: list = data[stamp]
```
