import numpy as np
from PIL import Image

# Line art: black rectangle on white background
img = np.ones((100, 100), dtype=np.uint8) * 255
img[20:80, 20:80] = 0
Image.fromarray(img).save("tests/fixtures/square_lineart.png")

# Photo-like: gradient with noise
rng = np.random.default_rng(42)
img2 = np.zeros((100, 100), dtype=np.uint8)
img2[25:75, 25:75] = 180
img2 = img2 + rng.integers(0, 30, size=(100, 100), dtype=np.uint8)
Image.fromarray(img2).save("tests/fixtures/noisy_photo.png")
