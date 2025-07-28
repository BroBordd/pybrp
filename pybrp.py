Z = lambda _:[0]*_
G_FREQS = [
    101342,9667,3497,1072,0,3793,*Z(2),2815,5235,*Z(3),3570,*Z(3),
    1383,*Z(3),2970,*Z(2),2857,*Z(8),1199,*Z(30),
    1494,1974,*Z(12),1351,*Z(122),1475,*Z(65)
]
CMD_NAMES={0:'BaseTimeStep',1:'StepSceneGraph',2:'AddSceneGraph',3:'RemoveSceneGraph',4:'AddNode',5:'NodeOnCreate',6:'SetForegroundScene',7:'RemoveNode',8:'AddMaterial',9:'RemoveMaterial',10:'AddMaterialComponent',11:'AddTexture',12:'RemoveTexture',13:'AddMesh',14:'RemoveMesh',15:'AddSound',16:'RemoveSound',17:'AddCollisionMesh',18:'RemoveCollisionMesh',19:'ConnectNodeAttribute',20:'NodeMessage',21:'SetNodeAttrFloat',22:'SetNodeAttrInt32',23:'SetNodeAttrBool',24:'SetNodeAttrFloats',25:'SetNodeAttrInt32s',26:'SetNodeAttrString',27:'SetNodeAttrNode',28:'SetNodeAttrNodeNull',29:'SetNodeAttrNodes',30:'SetNodeAttrPlayer',31:'SetNodeAttrPlayerNull',32:'SetNodeAttrMaterials',33:'SetNodeAttrTexture',34:'SetNodeAttrTextureNull',35:'SetNodeAttrTextures',36:'SetNodeAttrSound',37:'SetNodeAttrSoundNull',38:'SetNodeAttrSounds',39:'SetNodeAttrMesh',40:'SetNodeAttrMeshNull',41:'SetNodeAttrMeshes',42:'SetNodeAttrCollisionMesh',43:'SetNodeAttrCollisionMeshNull',44:'SetNodeAttrCollisionMeshes',45:'PlaySoundAtPosition',46:'PlaySound',47:'EmitBGDynamics',48:'EndOfFile',49:'DynamicsCorrection',50:'ScreenMessageBottom',51:'ScreenMessageTop',52:'AddData',53:'RemoveData',54:'CameraShake'}

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
    def decompress(self,src):
        if not src:return b''
        rem,comp=src[0]&15,src[0]>>7
        if not comp:return src
        out,ptr,l=bytearray(),src[1:],len(src)
        bl=((l-1)*8)-rem;bit=0
        while bit<bl:
            m_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
            if m_bit:
                n=510
                while n>=256:
                    if bit>=bl:raise ValueError("Incomplete Huffman code")
                    p_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
                    n=self.nodes[n].l if p_bit==0 else self.nodes[n].r
                out.append(n)
            else:
                if bit+8>bl:break
                bi,b_in_b=bit>>3,bit&7
                val=ptr[bi]if b_in_b==0 else(ptr[bi]>>b_in_b)|(ptr[bi+1]<<(8-b_in_b))
                out.append(val&255);bit+=8
        return bytes(out)

def get_data(_h, brp_path, progress=None):
    time_ms, out_data = 0, {}
    with open(brp_path, 'rb') as f:
        f.seek(0,2)
        total_size = f.tell()
        f.seek(6)
        while True:
            if progress: progress(f.tell(), total_size)
            b_data = f.read(1)
            if not b_data:
                break
            b1, comp_len = b_data[0], 0
            if b1 < 254:
                comp_len = b1
            elif b1 == 254:
                comp_len = int.from_bytes(f.read(2), 'little')
            else: # 255
                comp_len = int.from_bytes(f.read(4), 'little')
            if comp_len == 0:
                continue
            raw_msg = _h.decompress(f.read(comp_len))
            if not raw_msg or raw_msg[0] != 1:
                continue
            sub_off = 1
            while sub_off < len(raw_msg):
                try:
                    sub_size = int.from_bytes(raw_msg[sub_off:sub_off+2], 'little')
                except IndexError:
                    break
                except ValueError:
                    break
                sub_data = raw_msg[sub_off+2:sub_off+2+sub_size]
                if not sub_data:
                    sub_off += 2 + sub_size
                    continue
                cmd_id = sub_data[0]
                if cmd_id == 0:
                    time_ms += sub_data[1]
                else:
                    if time_ms not in out_data: out_data[time_ms] = []
                    out_data[time_ms].append({'name': CMD_NAMES.get(cmd_id, 'Unknown'), 'data_hex': sub_data.hex()})
                sub_off += 2 + sub_size
    if progress: progress(total_size, total_size)
    return out_data

def get_duration(_h, brp_path, progress=None):
    total_ms = 0
    with open(brp_path, 'rb') as f:
        f.seek(0,2)
        total_size = f.tell()
        f.seek(6)
        while True:
            if progress: progress(f.tell(), total_size)
            b_data = f.read(1)
            if not b_data:
                break
            b1, comp_len = b_data[0], 0
            if b1 < 254:
                comp_len = b1
            elif b1 == 254:
                comp_len = int.from_bytes(f.read(2), 'little')
            else: # 255
                comp_len = int.from_bytes(f.read(4), 'little')
            if comp_len == 0:
                continue
            raw_msg = _h.decompress(f.read(comp_len))
            if not raw_msg or raw_msg[0] != 1:
                continue
            sub_off = 1
            while sub_off < len(raw_msg):
                try:
                    sub_size = int.from_bytes(raw_msg[sub_off:sub_off+2], 'little')
                except IndexError:
                    break
                except ValueError:
                    break
                sub_data = raw_msg[sub_off+2:sub_off+2+sub_size]
                if sub_data and sub_data[0] == 0:
                    total_ms += sub_data[1]
                sub_off += 2 + sub_size
    if progress: progress(total_size, total_size)
    return total_ms

def decompress(_h, brp_path, output_path, progress=None):
    with open(brp_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
        f_in.seek(0,2)
        total_size = f_in.tell()
        f_out.write(f_in.read(6))
        while True:
            if progress: progress(f.tell(), total_size)
            b_data = f_in.read(1)
            if not b_data:
                break
            b1, m_len = b_data[0], 0
            if b1 < 254:
                m_len = b1
            elif b1 == 254:
                m_len = int.from_bytes(f_in.read(2), 'little')
            else: # 255
                m_len = int.from_bytes(f_in.read(4), 'little')
            if m_len > 0:
                decomp_data = _h.decompress(f_in.read(m_len))
                l32 = len(decomp_data)
                if l32 < 254:
                    f_out.write(bytes([l32]))
                elif l32 <= 65535:
                    f_out.write(bytes([254]));f_out.write(l32.to_bytes(2,'little'))
                else:
                    f_out.write(bytes([255]));f_out.write(l32.to_bytes(4,'little'))
                f_out.write(decomp_data)
    if progress: progress(total_size, total_size)
