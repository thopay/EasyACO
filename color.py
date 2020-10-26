from colorsys import hls_to_rgb, rgb_to_hls

def getBestColor(color):
    if color.startswith('#'):
        color = color[1:]
    r, g, b = [int(color[i:i+2], 16) for i in range(0, len(color), 2)]
    rb, gb, bb = 0, 0, 0
    l1 = (0.2126 * ((r/255)**2.2)) + (0.7152 * ((g/255)**2.2)) + (0.0722 * ((b/255)**2.2))
    l2 = (0.2126 * ((rb/255)**2.2)) + (0.7152 * ((gb/255)**2.2)) + (0.0722 * ((bb/255)**2.2))
    if l1 > l2:
        contrastRatio = int((l1 + 0.05) / (l2 + 0.05))
    else:
        contrastRatio = int((l2 + 0.05) / (l1 + 0.05))
    if contrastRatio > 5:
        return('#000000')
    else:
        return('#FFFFFF')