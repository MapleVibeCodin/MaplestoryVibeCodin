"""Click-through preview of the destination cell in the channel menu."""
from shop_pin import OverlayPin
from game_window import window_at_point

def preview_channel(channel, window, client):
    """Project a centered change-channel menu into overlay coordinates."""
    if not 1 <= channel <= 40 or window is None or client is None:
        return None
    left, top, width, height = window
    client_left, client_top, client_width, client_height = client
    if (client_width, client_height) not in {(1280, 720), (1366, 768)}:
        return None
    row, column = divmod(channel - 1, 8)
    # First cell is (361, 319) in the supplied 1280 × 720 game client.
    x = client_left - left + client_width // 2 - 279 + 70 * column
    y = client_top - top + client_height // 2 - 41 + 22 * row
    if not (0 <= x < x + 68 <= width and 0 <= y < y + 20 <= height):
        return None
    return x, y, x + 68, y + 20


class ChannelPin(OverlayPin):
    def __init__(self, master):
        super().__init__(master,interval_ms=25)

    def can_show(self, hwnd, rect, size, hits):
        if super().can_show(hwnd, rect, size, hits):
            return True
        left, top, width, height = rect
        sw, sh = size
        # A CHASE click can leave HeneFM in front. Show over exposed game
        # pixels only, including the space occupied by the arrow and label.
        for hit in hits.values():
            if hit['mode'] != 'GUIDE':
                return False
            l, t, r, b = hit['box']
            x1, x2 = left + l * width / sw, left + r * width / sw
            y1, y2 = top + t * height / sh, top + b * height / sh
            mid = (x1 + x2) / 2
            points = [(x, y) for x in (x1-6, mid, x2+6) for y in (y1-6, y2+6)]
            points.extend((x, y) for x in (mid-35, mid, mid+35) for y in (y1-66, y1-19))
            if any(window_at_point(round(x), round(y)) != hwnd for x, y in points):
                return False
        return bool(hits)

    def draw_markers(self,w,h,sw,sh,hits):
        c=self.canvas;c.delete('all');sx,sy=w/sw,h/sh
        for name,hit in hits.items():
            x,y,r,b=hit['box'];x*=sx;y*=sy;r*=sx;b*=sy
            if hit.get('mode')=='PRE':
                # No visual search needed: show the channel destination as
                # soon as HeneFM chooses it, even before menu appears.
                label='CHANGE TO '+name
                for color,width in [('#000000',9),('#ffffff',6),('#ffdb3d',3)]:
                    c.create_rectangle(x,y,r,b,outline=color,width=width)
                c.create_text((x+r)/2,(y+b)/2,text=label,fill='#ffe979',
                              font=('Segoe UI',11,'bold'))
                continue
            accent='#ffdb3d'
            for color,width in [('#000000',9),('#ffffff',6),(accent,3)]:
                c.create_rectangle(x-2,y-2,r+2,b+2,outline=color,width=width)
            cx=(x+r)/2
            for color,width in [('#000000',12),('#ffffff',8),(accent,5)]:
                c.create_line(cx,y-42,cx,y-5,fill=color,width=width,arrow='last',arrowshape=(12,15,8))
            c.create_text(cx,y-52,text=name,fill=accent,font=('Segoe UI',14,'bold'))
