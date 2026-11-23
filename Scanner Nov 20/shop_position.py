"""Project a HeneFM shop pin onto MapleStory's room-entry camera."""

# HeneFM renders both maps at 14/15 pixels per world unit and crops the
# vertical plot. Each tuple gives the world origin in plot pixels and the
# plot height. Both plots are 1600 px wide.
PLOTS = {'grass': (548, 564, 695), 'cave': (758, -792, 720)}

# The entrance's in01–in20 portals lead to out00 in each destination.
# OSMS Data Explorer's Classic portal atlas gives out00 at (1383, 888) in
# grass maps and (865, 856) in caves. Subtract the atlas origins (590, 855)
# and (815, -565) to use the same world coordinates as the HeneFM pins.
ENTRY_PORTAL = {'grass': (793, 33), 'cave': (50, 1421)}
ENTRY_CLIENTS = {(1280, 720), (1366, 768)}


def room_theme(room):
    if room is None or not 1 <= room <= 20:
        return None
    return 'grass' if room <= 6 or 13 <= room <= 16 else 'cave'


def read_shop_position(raw, room):
    """Keep an optional map pin without invalidating the rest of a listing."""
    theme = room_theme(room)
    if not isinstance(raw, dict) or theme is None or raw.get('theme') != theme:
        return None
    left, top = raw.get('left'), raw.get('top')
    if any(type(value) not in (float, int) or not 0 <= value <= 100 for value in (left, top)):
        return None
    return {'theme': theme, 'left': float(left), 'top': float(top)}


def world_shop_point(position):
    origin_x, origin_y, plot_height = PLOTS[position['theme']]
    return ((16 * position['left'] - origin_x) * 15 / 14,
            (plot_height * position['top'] / 100 - origin_y) * 15 / 14)


def entry_portal_point(room, client_size):
    """Return the portal threshold in the room's calibrated entry view."""
    width, height = client_size
    if room_theme(room) == 'grass':
        # Grass rooms are right/bottom clamped in the recorded entry views.
        # FM 1 shows the bottom platform close to the bottom of the client.
        return width - 225, height - (11 if room == 1 else 192)
    # The cave door stands on its own raised platform. FM 7 and FM 9 have
    # different vertical offsets in the supplied screenshot and entry clips.
    return width // 2 + 58, height // 2 + {7: 121, 9: 149}.get(room, 108)


def entry_shop_point(position, room, client_size, aligned_portal=None):
    """Return the seller's feet relative to the room portal on screen."""
    theme = room_theme(room)
    if client_size not in ENTRY_CLIENTS or theme != position['theme']:
        return None
    portal_x, portal_y = ENTRY_PORTAL[theme]
    shop_x, shop_y = world_shop_point(position)
    screen_x, screen_y = aligned_portal or entry_portal_point(room, client_size)
    return round(screen_x + shop_x - portal_x), round(screen_y + shop_y - portal_y)


def minimap_shop_marker(position, client, window):
    """Mark the target on the default minimap, which follows world coordinates."""
    # The default FM minimaps are placed at (32, 72) in the game client and
    # use 1:16 world scale. Their origins differ from the HeneFM map origins.
    client_x, client_y = client[:2]
    center_x, center_y = (438, 716) if position['theme'] == 'grass' else (649, -737)
    world_x, world_y = world_shop_point(position)
    x = (client_x - window[0]) + 32 + (world_x + center_x) / 16
    y = (client_y - window[1]) + 72 + (world_y + center_y) / 16
    return (round(x) - 6, round(y) - 6, round(x) + 6, round(y) + 6)


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
