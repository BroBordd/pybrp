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
            while sub_off + 2 <= len(raw_msg):
                sub_size_bytes = raw_msg[sub_off:sub_off+2]
                if len(sub_size_bytes) < 2:
                    break
                sub_size = int.from_bytes(sub_size_bytes, 'little')
                sub_off += 2
                if sub_off + sub_size > len(raw_msg):
                    break
                sub_data = raw_msg[sub_off:sub_off+sub_size]
                if len(sub_data) >= 2 and sub_data[0] == 0:
                    total_ms += sub_data[1]
                sub_off += sub_size
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

from struct import unpack

class _DataReader:
    def __init__(self, d): self.d,self.p=d,0
    def _r(self,n):
        if self.p+n>len(self.d): raise IndexError(f"Need {n} bytes, have {len(self.d)-self.p}")
        res=self.d[self.p:self.p+n];self.p+=n;return res
    def r_b(self): return unpack('<B',self._r(1))[0]
    def r_i(self): return unpack('<i',self._r(4))[0]
    def r_f(self): return unpack('<f',self._r(4))[0]
    def r_str(self): ln=unpack('<H',self._r(2))[0]; return self._r(ln).decode('utf-8','ignore')
    def r_arr_f(self): c=self.r_i(); return list(unpack(f'<{c}f',self._r(4*c)))
    def r_arr_i(self): c=self.r_i(); return list(unpack(f'<{c}i',self._r(4*c)))

def _p_add_node(d): return {'type_id':d.r_i(),'node_id':d.r_i()}
def _p_node_attr_f(d): return {'node_id':d.r_i(),'attr_id':d.r_i(),'value':d.r_f()}
def _p_node_attr_i(d): return {'node_id':d.r_i(),'attr_id':d.r_i(),'value':d.r_i()}
def _p_node_attr_b(d): return {'node_id':d.r_i(),'attr_id':d.r_i(),'value':bool(d.r_b())}
def _p_node_attr_str(d): return {'node_id':d.r_i(),'attr_id':d.r_i(),'value':d.r_str()}
def _p_node_attr_arr_f(d): return {'node_id':d.r_i(),'attr_id':d.r_i(),'values':d.r_arr_f()}
def _p_node_attr_arr_i(d): return {'node_id':d.r_i(),'attr_id':d.r_i(),'values':d.r_arr_i()}
def _p_node_message(d): n_id,m_id=d.r_i(),d.r_i(); return {'node_id':n_id,'msg_id':m_id,'raw_args_hex':d._r(len(d.d)-d.p).hex()}
def _p_sound_at_pos(d): return {'sound_id':d.r_i(),'volume':d.r_f(),'x':d.r_f(),'y':d.r_f(),'z':d.r_f()}
def _p_id(d): return {'id':d.r_i()}
def _p_id_attr(d): return {'id':d.r_i(),'attr_id':d.r_i()}
def _p_screen_msg(d): return {'value':d.r_str()}
def _p_cam_shake(d): return {'intensity':d.r_f()}

CMD_NAMES={0:'BaseTimeStep',1:'StepSceneGraph',2:'AddSceneGraph',3:'RemoveSceneGraph',4:'AddNode',5:'NodeOnCreate',6:'SetForegroundScene',7:'RemoveNode',8:'AddMaterial',9:'RemoveMaterial',10:'AddMaterialComponent',11:'AddTexture',12:'RemoveTexture',13:'AddMesh',14:'RemoveMesh',15:'AddSound',16:'RemoveSound',17:'AddCollisionMesh',18:'RemoveCollisionMesh',19:'ConnectNodeAttribute',20:'NodeMessage',21:'SetNodeAttrFloat',22:'SetNodeAttrInt32',23:'SetNodeAttrBool',24:'SetNodeAttrFloats',25:'SetNodeAttrInt32s',26:'SetNodeAttrString',27:'SetNodeAttrNode',28:'SetNodeAttrNodeNull',29:'SetNodeAttrNodes',30:'SetNodeAttrPlayer',31:'SetNodeAttrPlayerNull',32:'SetNodeAttrMaterials',33:'SetNodeAttrTexture',34:'SetNodeAttrTextureNull',35:'SetNodeAttrTextures',36:'SetNodeAttrSound',37:'SetNodeAttrSoundNull',38:'SetNodeAttrSounds',39:'SetNodeAttrMesh',40:'SetNodeAttrMeshNull',41:'SetNodeAttrMeshes',42:'SetNodeAttrCollisionMesh',43:'SetNodeAttrCollisionMeshNull',44:'SetNodeAttrCollisionMeshes',45:'PlaySoundAtPosition',46:'PlaySound',47:'EmitBGDynamics',48:'EndOfFile',49:'DynamicsCorrection',50:'ScreenMessageBottom',51:'ScreenMessageTop',52:'AddData',53:'RemoveData',54:'CameraShake'}
COMMAND_PARSERS={4:_p_add_node,5:_p_id,6:_p_id,7:_p_id,8:_p_id,9:_p_id,11:_p_id,12:_p_id,13:_p_id,14:_p_id,15:_p_id,16:_p_id,17:_p_id,18:_p_id,20:_p_node_message,21:_p_node_attr_f,22:_p_node_attr_i,23:_p_node_attr_b,24:_p_node_attr_arr_f,25:_p_node_attr_arr_i,26:_p_node_attr_str,27:_p_id_attr,28:_p_id_attr,29:_p_id_attr,30:_p_id_attr,31:_p_id_attr,32:_p_id_attr,33:_p_id_attr,34:_p_id_attr,35:_p_id_attr,36:_p_id_attr,37:_p_id_attr,38:_p_id_attr,39:_p_id_attr,40:_p_id_attr,41:_p_id_attr,42:_p_id_attr,43:_p_id_attr,44:_p_id_attr,45:_p_sound_at_pos,46:_p_id,50:_p_screen_msg,51:_p_screen_msg,52:_p_id,53:_p_id,54:_p_cam_shake}

def get_data(_h,brp_path,as_hex=False,progress=None):
    time_ms,out_data=0,{}
    with open(brp_path,'rb') as f:
        f.seek(0,2)
        total_size=f.tell()
        f.seek(6)
        while True:
            if progress:progress(f.tell(),total_size)
            b_data=f.read(1);
            if not b_data:break
            b1,comp_len=b_data[0],0
            if b1<254:comp_len=b1
            elif b1==254:comp_len=unpack('<H',f.read(2))[0]
            else:comp_len=unpack('<I',f.read(4))[0]
            if comp_len==0:continue
            raw_msg=_h.decompress(f.read(comp_len))
            if not raw_msg or raw_msg[0]!=1:continue
            sub_off=1
            while sub_off<len(raw_msg):
                try:sub_size=unpack('<H',raw_msg[sub_off:sub_off+2])[0]
                except:break
                sub_data=raw_msg[sub_off+2:sub_off+2+sub_size]
                if not sub_data:
                    sub_off+=2+sub_size;continue
                cmd_id=sub_data[0]
                if cmd_id==0:
                    time_ms+=sub_data[1]
                else:
                    if time_ms not in out_data:out_data[time_ms]=[]
                    payload={'name':CMD_NAMES.get(cmd_id,'Unknown')}
                    if as_hex:payload['data_hex']=sub_data.hex()
                    else:
                        parser=COMMAND_PARSERS.get(cmd_id)
                        if parser:
                            try:payload['args']=parser(_DataReader(sub_data[1:]))
                            except Exception as e:payload['args']=f'(parse_error: {e})';payload['data_hex']=sub_data.hex()
                        else:payload['data_hex']=sub_data.hex()
                    out_data[time_ms].append(payload)
                sub_off+=2+sub_size
    if progress:progress(total_size,total_size)
    return out_data
