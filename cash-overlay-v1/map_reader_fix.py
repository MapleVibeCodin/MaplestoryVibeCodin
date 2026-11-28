"""Pinned upstream map-reader compatibility fix and stable-title qualification."""
def patch_reader_source(source):
    # None is an intentionally hidden control window, not an uninitialized reader.
    old="        if self.own_rect is None:\n            return None, None                   # wait until we know where this app's window is\n"
    if source.count(old)!=1:
        raise ValueError("Pinned upstream map-reader guard changed")
    return source.replace(old,"",1)

def stable_map_timestamp(reader,map_name,now):
    """Refresh from the observed title fingerprint, not the infrequent OCR event."""
    seen=getattr(reader,"map_seen_at",None)
    look=getattr(reader,"map_look",None)
    if not map_name or not getattr(reader,"map_box",None) or getattr(reader,"map_unread",True):
        return None
    if getattr(reader,"map_print",None) is None or not isinstance(look,dict) or not look.get("text"):
        return None
    if type(seen) not in (float,int) or not 0<=now-seen<=3:
        return None
    return seen
