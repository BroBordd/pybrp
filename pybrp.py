from struct import unpack

Z = lambda _:[0]*_
G_FREQS = [
    101342,9667,3497,1072,0,3793,*Z(2),2815,5235,*Z(3),3570,*Z(3),
    1383,*Z(3),2970,*Z(2),2857,*Z(8),1199,*Z(30),
    1494,1974,*Z(12),1351,*Z(122),1475,*Z(65)
]

class _H:
    class _N:
        def __init__(self):
            self.l,self.r,self.p,self.f=-1,-1,0,0
    def __init__(self):
        self.nodes=[self._N()for _ in range(511)]
        for i in range(256):self.nodes[i].f=G_FREQS[i]
        nc=256
        while nc<511:
            s1,s2=-1,-1
            i=0
            while self.nodes[i].p!=0:i+=1
            s1=i;i+=1
            while self.nodes[i].p!=0:i+=1
            s2=i;i+=1
            while i<nc:
                if self.nodes[i].p==0:
                    if self.nodes[s1].f>self.nodes[s2].f:
                        if self.nodes[i].f<self.nodes[s1].f:s1=i
                    elif self.nodes[i].f<self.nodes[s2].f:s2=i
                i+=1
            self.nodes[nc].f=self.nodes[s1].f+self.nodes[s2].f
            self.nodes[s1].p=self.nodes[s2].p=nc-255
            self.nodes[nc].r,self.nodes[nc].l=s1,s2
            nc+=1
    _T = None
    def _tables(self):
        """Lookup tables over a 16 bit window (flag bit + <=15 bit code): for every
        window, all complete symbols it holds and the bits they use. Built once."""
        T = type(self)._T
        if T is not None: return T
        nodes = self.nodes
        def one(w, pos):
            if pos >= 16: return None
            if (w >> pos) & 1:
                n, q = 510, pos + 1
                while n >= 256:
                    if q >= 16: return None
                    n = nodes[n].l if not (w >> q) & 1 else nodes[n].r
                    q += 1
                return n, q
            if pos + 9 > 16: return None
            return (w >> (pos + 1)) & 255, pos + 9
        M, ML = [b''] * 65536, [0] * 65536
        for w in range(65536):
            pos, syms = 0, bytearray()
            while True:
                r = one(w, pos)
                if r is None: break
                syms.append(r[0]); pos = r[1]
            M[w], ML[w] = bytes(syms), pos
        type(self)._T = T = (M, ML)
        return T
    def decompress(self, src):
        if not src: return b''
        rem, comp = src[0] & 15, src[0] >> 7
        if not comp: return src
        bl = (len(src) - 1) * 8 - rem
        p = src[1:] + b'\0\0\0'
        M, ML = self._tables()
        out = bytearray()
        bit = 0
        lim = bl - 16
        while bit <= lim:  # fast path: whole 16 bit window is real data
            bi = bit >> 3
            w = ((p[bi] | p[bi+1] << 8 | p[bi+2] << 16) >> (bit & 7)) & 0xFFFF
            out += M[w]
            bit += ML[w]
        nodes = self.nodes
        while bit < bl:  # tail (<16 bits), bit exact like the original decoder
            if (p[bit >> 3] >> (bit & 7)) & 1:
                bit += 1
                n = 510
                while n >= 256:
                    if bit >= bl: raise ValueError("Incomplete Huffman code")
                    n = nodes[n].l if not (p[bit >> 3] >> (bit & 7)) & 1 else nodes[n].r
                    bit += 1
                out.append(n)
            else:
                bit += 1
                if bit + 8 > bl: break
                bi, bb = bit >> 3, bit & 7
                out.append((p[bi] if bb == 0 else (p[bi] >> bb) | (p[bi+1] << (8 - bb))) & 255)
                bit += 8
        return bytes(out)


# ---------------------------------------------------------------------------
# .brp file layout (BombSquad / Ballistica 1.7 and 1.8)
#
#   u32  file id (83749)
#   u16  protocol version of the recorded stream
#   -- protocol >= 39 only: asset-package listing --
#   u32  package count, then per package: u32 length + apverid bytes
#   -- then a sequence of messages --
#   1/3/5 byte length prefix (<254 | 254 + u16 | 255 + u32), then the
#   (Huffman-compressed or raw) message. Message type 1 carries a run of
#   [length][command] pairs:
#       protocol < 44 : u16 length, every integer is a fixed int32
#       protocol >= 44: varint length, every integer is a zigzag varint
#   Protocol 44+ may also fold time steps into other commands (see
#   _step_ms), which is what made 1.7-era duration scanning return 0.
# ---------------------------------------------------------------------------

BRP_FILE_ID = 83749
PROTO_CLIENT_MIN = 24      # oldest stream the game still plays
PROTO_DEV_GAP = (38, 55)   # 1.8 development protocols; the game refuses these
PROTO_PACKAGES = 39        # header asset-package listing starts here
PROTO_COMPACT = 44         # varint framing + merged commands start here
MAX_PACKAGES = 4096
MAX_APVERID = 1024

CMD_NAMES = {
    0: 'BaseTimeStep', 1: 'StepSceneGraph', 2: 'AddSceneGraph', 3: 'RemoveSceneGraph',
    4: 'AddNode', 5: 'NodeOnCreate', 6: 'SetForegroundScene', 7: 'RemoveNode',
    8: 'AddMaterial', 9: 'RemoveMaterial', 10: 'AddMaterialComponent', 11: 'AddTexture',
    12: 'RemoveTexture', 13: 'AddMesh', 14: 'RemoveMesh', 15: 'AddSound', 16: 'RemoveSound',
    17: 'AddCollisionMesh', 18: 'RemoveCollisionMesh', 19: 'ConnectNodeAttribute',
    20: 'NodeMessage', 21: 'SetNodeAttrFloat', 22: 'SetNodeAttrInt32', 23: 'SetNodeAttrBool',
    24: 'SetNodeAttrFloats', 25: 'SetNodeAttrInt32s', 26: 'SetNodeAttrString',
    27: 'SetNodeAttrNode', 28: 'SetNodeAttrNodeNull', 29: 'SetNodeAttrNodes',
    30: 'SetNodeAttrPlayer', 31: 'SetNodeAttrPlayerNull', 32: 'SetNodeAttrMaterials',
    33: 'SetNodeAttrTexture', 34: 'SetNodeAttrTextureNull', 35: 'SetNodeAttrTextures',
    36: 'SetNodeAttrSound', 37: 'SetNodeAttrSoundNull', 38: 'SetNodeAttrSounds',
    39: 'SetNodeAttrMesh', 40: 'SetNodeAttrMeshNull', 41: 'SetNodeAttrMeshes',
    42: 'SetNodeAttrCollisionMesh', 43: 'SetNodeAttrCollisionMeshNull',
    44: 'SetNodeAttrCollisionMeshes', 45: 'PlaySoundAtPosition', 46: 'PlaySound',
    47: 'EmitBGDynamics', 48: 'EndOfFile', 49: 'DynamicsCorrection',
    50: 'ScreenMessageBottom', 51: 'ScreenMessageTop', 52: 'AddData', 53: 'RemoveData',
    54: 'CameraShake',
    # 1.8 additions (protocol 39+)
    55: 'DeclareAssetPackage', 56: 'AddTextureIndexed', 57: 'AddMeshIndexed',
    58: 'AddSoundIndexed', 59: 'AddCollisionMeshIndexed', 60: 'InputDeviceFeedback',
    61: 'AddSpazDef', 62: 'RemoveSpazDef', 63: 'SetNodeAttrSpazDef',
    64: 'SetNodeAttrSpazDefNull', 65: 'StepSceneGraphAndTime', 66: 'AddAnimCurve',
    67: 'TimeStepSceneGraphAndTime', 68: 'AddNodeWithAttrs', 69: 'AddDepiction',
    70: 'RemoveDepiction', 71: 'SetNodeAttrDepiction', 72: 'SetNodeAttrDepictionNull',
    73: 'ScreenMessageTopDepiction', 74: 'PlaySoundEx', 75: 'PlaySoundAtPositionEx',
}

C_TIME, C_STEP, C_STEP_TIME, C_TIME_STEP_TIME, C_ADD_NODE_ATTRS = 0, 1, 65, 67, 68


# ----------------------------- header / framing -----------------------------

def is_supported_protocol(version):
    """Mirror of the game's IsJoinableHostProtocol (minus the upper cap, so
    newer streams are still attempted rather than refused)."""
    return version >= PROTO_CLIENT_MIN and not (PROTO_DEV_GAP[0] <= version <= PROTO_DEV_GAP[1])

def _read_exact(f, n, what):
    d = f.read(n)
    if len(d) != n:
        raise ValueError(f"truncated .brp file while reading {what}")
    return d

def read_header(f):
    """Read the header from an open binary file positioned at 0.
    Returns {'version', 'compact', 'packages', 'data_offset'} and leaves the
    file positioned at the first message. Raises ValueError if the file is not
    a readable replay (instead of silently yielding nothing)."""
    fid = unpack('<I', _read_exact(f, 4, 'file id'))[0]
    if fid != BRP_FILE_ID:
        raise ValueError(f"not a .brp file (file id {fid}, expected {BRP_FILE_ID})")
    version = unpack('<H', _read_exact(f, 2, 'protocol version'))[0]
    if not is_supported_protocol(version):
        raise ValueError(f"unsupported replay protocol {version} "
                         f"(supported: {PROTO_CLIENT_MIN}-37 and 56+)")
    packages = []
    if version >= PROTO_PACKAGES:
        count = unpack('<I', _read_exact(f, 4, 'package count'))[0]
        if count > MAX_PACKAGES:
            raise ValueError(f"corrupt asset-package listing (count {count})")
        for _ in range(count):
            ln = unpack('<I', _read_exact(f, 4, 'package length'))[0]
            if ln > MAX_APVERID:
                raise ValueError(f"corrupt asset-package listing (length {ln})")
            packages.append(_read_exact(f, ln, 'package id').decode('utf-8', 'replace') if ln else '')
    return {'version': version, 'compact': version >= PROTO_COMPACT,
            'packages': packages, 'data_offset': f.tell()}

def get_info(brp_path):
    """Header info for a replay: protocol version, packages, etc."""
    with open(brp_path, 'rb') as f:
        return read_header(f)

def _iter_messages(f, _h, total_size, progress=None):
    """Yield each decompressed message. A truncated final message (e.g. a
    replay still being written) ends iteration instead of raising."""
    while True:
        if progress: progress(f.tell(), total_size)
        b = f.read(1)
        if not b: break
        b1 = b[0]
        if b1 < 254: n = b1
        elif b1 == 254:
            d = f.read(2)
            if len(d) < 2: break
            n = unpack('<H', d)[0]
        else:
            d = f.read(4)
            if len(d) < 4: break
            n = unpack('<I', d)[0]
        if n == 0: continue
        data = f.read(n)
        if len(data) < n: break
        yield _h.decompress(data)

def _varint(b, p):
    v = shift = 0
    while True:
        if p >= len(b) or shift > 28: raise IndexError('bad varint')
        x = b[p]; p += 1
        v |= (x & 0x7f) << shift
        if not x & 0x80: return v, p
        shift += 7

def _zz(b, p):
    v, p = _varint(b, p)
    return (v >> 1) ^ -(v & 1), p

def _iter_commands(raw, compact):
    """Yield each command (id byte + args) of a type-1 message."""
    off = 1
    while off < len(raw):
        try:
            if compact: size, off = _varint(raw, off)
            else:
                if off + 2 > len(raw): return
                size = unpack('<H', raw[off:off + 2])[0]; off += 2
        except IndexError:
            return
        if off + size > len(raw): return
        if size: yield raw[off:off + size]
        off += size

def _step_ms(cmd, compact):
    """(ms before the command's scene step, ms after) for the commands that
    advance time, else None. Plain BaseTimeStep is all 'before'; the merged
    1.8 forms carry the delta inside the command."""
    try:
        c = cmd[0]
        if c == C_TIME:
            return ((_zz(cmd, 1)[0] if compact else unpack('<i', cmd[1:5])[0]), 0)
        if compact and c == C_STEP_TIME:
            _, p = _zz(cmd, 1)           # scene id
            return (0, _zz(cmd, p)[0])
        if compact and c == C_TIME_STEP_TIME:
            pre, p = _zz(cmd, 1)
            _, p = _zz(cmd, p)           # scene id
            return (pre, _zz(cmd, p)[0])
    except (IndexError, ValueError, Exception):
        return None
    return None


# --------------------------------- public API -------------------------------

def _scan_ms(raw, compact):
    """Total ms advanced by one type-1 message; same result as summing
    _step_ms over _iter_commands, but only parses the time commands."""
    total, off, n = 0, 1, len(raw)
    while off < n:
        if compact:
            b = raw[off]
            if b < 128:
                size = b; off += 1
            else:
                try: size, off = _varint(raw, off)
                except IndexError: return total
        else:
            if off + 2 > n: return total
            size = raw[off] | raw[off+1] << 8; off += 2
        if off + size > n: return total
        if size:
            c = raw[off]
            if c == 0 or (compact and (c == C_STEP_TIME or c == C_TIME_STEP_TIME)):
                s = _step_ms(raw[off:off+size], compact)
                if s: total += s[0] + s[1]
        off += size
    return total

def get_duration(_h, brp_path, progress=None):
    """Total duration in ms. Raises ValueError on unreadable/unsupported files."""
    total_ms = 0
    with open(brp_path, 'rb') as f:
        f.seek(0, 2); total_size = f.tell(); f.seek(0)
        compact = read_header(f)['compact']
        for raw in _iter_messages(f, _h, total_size, progress):
            if not raw or raw[0] != 1: continue
            total_ms += _scan_ms(raw, compact)
    if progress: progress(total_size, total_size)
    return total_ms

def decompress(_h, brp_path, output_path, progress=None):
    """Write a copy of the replay with every message decompressed. The header
    (including the 1.8 package listing) is copied verbatim."""
    with open(brp_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
        f_in.seek(0, 2); total_size = f_in.tell(); f_in.seek(0)
        off = read_header(f_in)['data_offset']
        f_in.seek(0); f_out.write(f_in.read(off))
        for raw in _iter_messages(f_in, _h, total_size, progress):
            l = len(raw)
            if l < 254: f_out.write(bytes([l]))
            elif l <= 65535: f_out.write(b'\xfe' + l.to_bytes(2, 'little'))
            else: f_out.write(b'\xff' + l.to_bytes(4, 'little'))
            f_out.write(raw)
    if progress: progress(total_size, total_size)


class _DataReader:
    """Reads command arguments with either the fixed (<44) or compact (>=44)
    integer layout. Floats and raw bytes are the same in both."""
    def __init__(self, d, compact=False): self.d, self.p, self.c = d, 0, compact
    def _r(self, n):
        if self.p + n > len(self.d): raise IndexError(f"Need {n} bytes, have {len(self.d)-self.p}")
        res = self.d[self.p:self.p + n]; self.p += n; return res
    def left(self): return len(self.d) - self.p
    def rest(self): return self._r(self.left())
    def r_i(self):
        if self.c:
            v, self.p = _zz(self.d, self.p); return v
        return unpack('<i', self._r(4))[0]
    def r_f(self): return unpack('<f', self._r(4))[0]
    def r_b(self): return bool(self.r_i())
    def r_str(self):
        n = self.r_i()
        if n < 0: raise ValueError('negative string length')
        return self._r(n).decode('utf-8', 'ignore')
    def r_arr_f(self): c = self.r_i(); return list(unpack(f'<{c}f', self._r(4 * c)))
    def r_arr_i(self): c = self.r_i(); return [self.r_i() for _ in range(c)]

def _p_id(d): return {'id': d.r_i()}
def _p_scene_id(d): return {'scene_id': d.r_i()}
def _p_add_scene(d): return {'scene_id': d.r_i(), 'start_time': d.r_i()}
def _p_add_node(d): return {'scene_id': d.r_i(), 'type_id': d.r_i(), 'node_id': d.r_i()}
def _p_add_res(d): return {'scene_id': d.r_i(), 'id': d.r_i()}
def _p_add_named(d): return {'scene_id': d.r_i(), 'id': d.r_i(), 'name': d.r_str()}
def _p_add_indexed(d): return {'scene_id': d.r_i(), 'id': d.r_i(), 'package_index': d.r_i(), 'asset_index': d.r_i()}
def _p_add_json(d): return {'scene_id': d.r_i(), 'id': d.r_i(), 'json': d.r_str()}
def _p_connect(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'to_node_id': d.r_i(), 'to_attr_id': d.r_i()}
def _p_attr_f(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'value': d.r_f()}
def _p_attr_i(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'value': d.r_i()}
def _p_attr_b(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'value': d.r_b()}
def _p_attr_str(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'value': d.r_str()}
def _p_attr_arr_f(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'values': d.r_arr_f()}
def _p_attr_arr_i(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'values': d.r_arr_i()}
def _p_attr_ref(d): return {'node_id': d.r_i(), 'attr_id': d.r_i(), 'value': d.r_i()}
def _p_attr_null(d): return {'node_id': d.r_i(), 'attr_id': d.r_i()}
def _p_node_message(d):
    n_id, size = d.r_i(), d.r_i()
    return {'node_id': n_id, 'size': size, 'raw_args_hex': d.rest().hex()}
def _p_sound_at_pos(d): return {'sound_id': d.r_i(), 'volume': d.r_f(), 'x': d.r_f(), 'y': d.r_f(), 'z': d.r_f()}
def _p_play_sound(d): return {'sound_id': d.r_i(), 'volume': d.r_f()}
def _p_screen_bottom(d):
    s = d.r_str(); return {'value': s, 'color': [d.r_f() for _ in range(3)]}
def _p_screen_top(d):
    tex, tint = d.r_i(), d.r_i(); s = d.r_str()
    n = 3 * 4 if d.left() >= 48 else 3 * 3   # 12 floats from protocol 48, else 9
    return {'texture_id': tex, 'tint_texture_id': tint, 'value': s,
            'floats': [d.r_f() for _ in range(n)]}
def _p_screen_top_depiction(d):
    dep = d.r_i(); s = d.r_str()
    return {'depiction_id': dep, 'value': s, 'color': [d.r_f() for _ in range(3)]}
def _p_cam_shake(d): return {'intensity': d.r_f()}
def _p_declare_pkg(d): return {'index': d.r_i(), 'total': d.r_i(), 'apverid': d.r_str()}
def _p_feedback(d): return {'player_id': d.r_i(), 'payload': d.r_str()}
def _p_add_node_attrs(d):
    return {'scene_id': d.r_i(), 'type_id': d.r_i(), 'node_id': d.r_i(),
            'attr_count': d.r_i(), 'packed_attrs_hex': d.rest().hex()}

COMMAND_PARSERS = {
    1: _p_scene_id, 2: _p_add_scene, 3: _p_id, 4: _p_add_node, 5: _p_id, 6: _p_scene_id, 7: _p_id,
    8: _p_add_res, 9: _p_id, 11: _p_add_named, 12: _p_id, 13: _p_add_named, 14: _p_id,
    15: _p_add_named, 16: _p_id, 17: _p_add_named, 18: _p_id, 19: _p_connect, 20: _p_node_message,
    21: _p_attr_f, 22: _p_attr_i, 23: _p_attr_b, 24: _p_attr_arr_f, 25: _p_attr_arr_i,
    26: _p_attr_str, 27: _p_attr_ref, 28: _p_attr_null, 31: _p_attr_null, 34: _p_attr_null,
    37: _p_attr_null, 40: _p_attr_null, 43: _p_attr_null, 64: _p_attr_null, 72: _p_attr_null,
    30: _p_attr_ref, 33: _p_attr_ref, 36: _p_attr_ref, 39: _p_attr_ref, 42: _p_attr_ref,
    63: _p_attr_ref, 71: _p_attr_ref,
    45: _p_sound_at_pos, 46: _p_play_sound, 50: _p_screen_bottom, 51: _p_screen_top,
    54: _p_cam_shake, 55: _p_declare_pkg, 56: _p_add_indexed, 57: _p_add_indexed,
    58: _p_add_indexed, 59: _p_add_indexed, 60: _p_feedback, 61: _p_add_json, 62: _p_id,
    68: _p_add_node_attrs, 69: _p_add_json, 70: _p_id, 73: _p_screen_top_depiction,
}

def get_data(_h, brp_path, as_hex=False, progress=None):
    """{time_ms: [command dicts]}. Time-advancing commands (including the 1.8
    merged forms) move the clock; merged step commands are reported as a
    'StepSceneGraph' entry, like the separate commands they stand for."""
    time_ms, out = 0, {}
    def add(cmd_id, name, cmd, args=None):
        payload = {'name': name}
        if as_hex: payload['data_hex'] = cmd.hex()
        else:
            parser = COMMAND_PARSERS.get(cmd_id)
            if args is not None: payload['args'] = args
            elif parser:
                try: payload['args'] = parser(_DataReader(cmd[1:], compact))
                except Exception as e:
                    payload['args'] = f'(parse_error: {e})'; payload['data_hex'] = cmd.hex()
            else: payload['data_hex'] = cmd.hex()
        out.setdefault(time_ms, []).append(payload)
    with open(brp_path, 'rb') as f:
        f.seek(0, 2); total_size = f.tell(); f.seek(0)
        compact = read_header(f)['compact']
        for raw in _iter_messages(f, _h, total_size, progress):
            if not raw or raw[0] != 1: continue
            for cmd in _iter_commands(raw, compact):
                cid = cmd[0]
                s = _step_ms(cmd, compact)
                if s is None:
                    add(cid, CMD_NAMES.get(cid, 'Unknown'), cmd)
                    continue
                time_ms += s[0]
                if cid in (C_STEP_TIME, C_TIME_STEP_TIME):
                    p = 1 if cid == C_STEP_TIME else _varint(cmd, 1)[1]
                    add(C_STEP, 'StepSceneGraph', cmd, None if as_hex else {'scene_id': _zz(cmd, p)[0]})
                time_ms += s[1]
    if progress: progress(total_size, total_size)
    return out

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        sys.exit('usage: pybrp.py replay.brp')
    info = get_info(sys.argv[1])
    ms = get_duration(_H(), sys.argv[1])
    print(f"protocol {info['version']}, {len(info['packages'])} asset package(s), "
          f"{'compact' if info['compact'] else 'fixed'} framing, duration {ms} ms")
