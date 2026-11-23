"""Project a HeneFM shop pin onto MapleStory's room-entry camera."""

# HeneFM renders both maps at 14/15 pixels per world unit and crops the
# vertical plot. Each tuple gives the world origin in plot pixels and the
# plot height. Both plots are 1600 px wide.
PLOTS = {'grass': (548, 564, 695), 'cave': (758, -792, 720)}

# World coordinates at the center of the room-entry view, calibrated against
# the supplied room screenshots and entry recordings. Shops remain stationary
# in world coordinates, but the view can change as the player moves.
ENTRY_CENTERS = {'grass': (326, -143), 'cave': (-8, 1313)}
ENTRY_CLIENTS = {(1280, 720), (1366, 768)}


def read_shop_position(raw, room):
    """Keep an optional map pin without invalidating the rest of a listing."""
    if not isinstance(raw, dict) or room is None:
        return None
    theme = 'grass' if room <= 6 or 13 <= room <= 16 else 'cave'
    if raw.get('theme') != theme:
        return None
    left, top = raw.get('left'), raw.get('top')
    if any(type(value) not in (float, int) or not 0 <= value <= 100 for value in (left, top)):
        return None
    return {'theme': theme, 'left': float(left), 'top': float(top)}


def entry_shop_point(position, client_size):
    """Return the seller's feet in client pixels at room entry."""
    if client_size not in ENTRY_CLIENTS:
        return None
    theme = position['theme']
    origin_x, origin_y, plot_height = PLOTS[theme]
    world_x = (16 * position['left'] - origin_x) * 15 / 14
    world_y = (plot_height * position['top'] / 100 - origin_y) * 15 / 14
    camera_x, camera_y = ENTRY_CENTERS[theme]
    width, height = client_size
    return round(width / 2 + world_x - camera_x), round(height / 2 + world_y - camera_y)


def shop_marker(point, client, window):
    """Build an on-screen box or an edge cue if the shop starts out of view."""
    x, feet = point
    left, top, width, height = client
    dx, dy = left - window[0], top - window[1]
    y = feet - 52
    if 4 <= x <= width - 4 and 4 <= y <= height - 4:
        box = (max(6, x - 77), max(6, feet - 120),
               min(width - 6, x + 77), min(height - 6, feet + 17))
        if box[2] > box[0] and box[3] > box[1]:
            l, t, r, b = box
            return (l + dx, t + dy, r + dx, b + dy), 'SHOP'

    if x < 4:
        direction = 'LEFT'
    elif x > width - 4:
        direction = 'RIGHT'
    elif y < 4:
        direction = 'UP'
    else:
        direction = 'DOWN'
    x = min(width - 145, max(145, x)) + dx
    y = min(height - 30, max(55, y)) + dy
    return (x - 115, y - 16, x + 115, y + 16), direction
