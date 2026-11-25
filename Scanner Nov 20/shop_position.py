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
        # Use the updated entry camera measurements where a screenshot exists.
        # FM 4: 142 client px downward correction from the Nov 26 entry screenshot.
        bottom_margin = {1: 11, 2: 44, 3: 48, 4: 50, 5: 45, 6: 8, 13: 47, 14: 48, 15: 40}.get(room, 192)
        return width - 225, height - bottom_margin
    # The cave door stands on its own raised platform. Use the vertical
    # offset measured for each room where an entry view is available.
    # FM9 native 1366x768 screenshot: doorway bottom center ~633,488.
    # Previous estimate (741,533) projected a partly visible shop beyond right edge.
    if room == 9 and client_size == (1366, 768):
        return 633, 488
    return width // 2 + 58, height // 2 + {7: 121, 9: 149, 11: 97, 17: 97}.get(room, 108)


def entry_shop_point(position, room, client_size, aligned_portal=None):
    """Return the seller's feet relative to the room portal on screen."""
    theme = room_theme(room)
    if client_size not in ENTRY_CLIENTS or theme != position['theme']:
        return None
    portal_x, portal_y = ENTRY_PORTAL[theme]
    shop_x, shop_y = world_shop_point(position)
    screen_x, screen_y = aligned_portal or entry_portal_point(room, client_size)
    return round(screen_x + shop_x - portal_x), round(screen_y + shop_y - portal_y)


def _shop_sign_bounds(point):
    x, feet = point
    # This part of the sign is shared by player-shop bubbles and merchant
    # boards. Exclude the avatar, platform, and the rest of the booth.
    return x - 50, feet - 125, x + 50, feet - 94


def shop_marker(point, client, window):
    """Outline the clickable part of the shop sign at the projected position."""
    left, top, width, height = client
    # Keep the visible part of a sign that extends past the client edge.
    l, t, r, b = _shop_sign_bounds(point)
    l, t = max(2, l), max(2, t)
    r, b = min(width - 2, r), min(height - 2, b)
    if r <= l or b <= t:
        return None
    dx, dy = left - window[0], top - window[1]
    return l + dx, t + dy, r + dx, b + dy


def shop_offscreen_notice(point, client_size):
    """Describe which edge the shop sign lies beyond."""
    width, height = client_size
    l, t, r, b = _shop_sign_bounds(point)
    if b <= 2:
        return 'Shop sign above view'
    if t >= height - 2:
        return 'Shop sign below view'
    if r <= 2:
        return 'Shop sign left of view'
    if l >= width - 2:
        return 'Shop sign right of view'
    return 'Shop sign outside view'
