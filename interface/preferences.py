(HEIGHT, WIDTH) = (20, 100)

# colors
colors = {
    15: (255, 0, 0),  # foreground
    14: (255, 133, 0),  # background
    13: (255, 193, 0),  # active background
    12: (0, 0, 255),  # active foreground
    11: (178, 178, 178),  # menu background
    10: (0, 0, 0),  # menu foreground
    9: (11, 102, 0),  # menu active foreground
}

# color_pairs
# (foreground, background)
color_pairs = {
    1: (15, 14),  # standart scheme
    2: (15, 13),  # active window/line
    3: (12, 14),  # current song and inactive line
    4: (12, 13),  # current song and active line
    5: (15, 12),  # active fragment
    15: (10, 11),  # scheme for menu
    14: (9, 11),  # scheme for active menu button
}

for i in colors:
    col1 = int(colors[i][0] * 1000 / 255)
    col2 = int(colors[i][1] * 1000 / 255)
    col3 = int(colors[i][2] * 1000 / 255)
    colors[i] = (col1, col2, col3)