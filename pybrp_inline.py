from struct import unpack
from io import BytesIO

Z = lambda _:_*[0]
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
                    if bit>=bl:raise ValueError("A")
                    p_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
                    n=self.nodes[n].l if p_bit==0 else self.nodes[n].r
                out.append(n)
            else:
                if bit+8>bl:break
                bi,b_in_b=bit>>3,bit&7
                val=ptr[bi]if b_in_b==0 else(ptr[bi]>>b_in_b)|(ptr[bi+1]<<(8-b_in_b))
                out.append(val&255);bit+=8
        return bytes(out)
_huffman=_H()
def decompress_brp(brp_path):
    raw_out=BytesIO()
    with open(brp_path,'rb')as f:
        raw_out.write(f.read(6))
        while True:
            b_data=f.read(1)
            if not b_data:break
            b1,m_len=b_data[0],0
            if b1<254:m_len=b1
            elif b1==254:m_len=unpack('<H',f.read(2))[0]
            else:m_len=unpack('<I',f.read(4))[0]
            if m_len>0:
                decomp_data=_huffman.decompress(f.read(m_len))
                l32=len(decomp_data)
                if l32<254:raw_out.write(bytes([l32]))
                elif l32<=65535:raw_out.write(bytes([254]));raw_out.write(l32.to_bytes(2,'little'))
                else:raw_out.write(bytes([255]));raw_out.write(l32.to_bytes(4,'little'))
                raw_out.write(decomp_data)
    return raw_out.getvalue()
def get_replay_duration(raw_data):
    total_ms=0
    f=BytesIO(raw_data)
    f.seek(6)
    while True:
        b_data=f.read(1)
        if not b_data:break
        b1,msg_len=b_data[0],0
        if b1<254:msg_len=b1
        elif b1==254:msg_len=unpack('<H',f.read(2))[0]
        else:msg_len=unpack('<I',f.read(4))[0]
        msg_data=f.read(msg_len)
        if not msg_data or msg_data[0]!=1:continue
        sub_off=1
        while sub_off<len(msg_data):
            try:sub_size=unpack('<H',msg_data[sub_off:sub_off+2])[0]
            except:break
            sub_data=msg_data[sub_off+2:sub_off+2+sub_size]
            if sub_data and sub_data[0]==0:total_ms+=sub_data[1]
            sub_off+=2+sub_size
    return total_ms/1000.0
