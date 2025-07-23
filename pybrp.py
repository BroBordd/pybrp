from struct import unpack, pack, error
import os

# region Decompression Code
G_FREQS = [
    101342, 9667, 3497, 1072, 0, 3793, 0, 0, 2815, 5235, 0, 0, 0, 3570, 0, 0,
    0, 1383, 0, 0, 0, 2970, 0, 0, 2857, 0, 0, 0, 0, 0, 0, 0,
    0, 1199, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1494,
    1974, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1351, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1475,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
]

class Huffman:
    class Node:
        def __init__(self):
            self.left_child = -1
            self.right_child = -1
            self.parent = 0
            self.frequency = 0

    def __init__(self):
        self.nodes = [self.Node() for _ in range(511)]
        self._build()

    def _build(self):
        for i in range(256):
            self.nodes[i].frequency = G_FREQS[i]

        node_count = 256
        while node_count < 511:
            smallest1 = -1
            smallest2 = -1
            
            i = 0
            while self.nodes[i].parent != 0: i += 1
            smallest1 = i
            i += 1
            while self.nodes[i].parent != 0: i += 1
            smallest2 = i
            i += 1
            
            while i < node_count:
                if self.nodes[i].parent == 0:
                    if self.nodes[smallest1].frequency > self.nodes[smallest2].frequency:
                        if self.nodes[i].frequency < self.nodes[smallest1].frequency:
                            smallest1 = i
                    else:
                        if self.nodes[i].frequency < self.nodes[smallest2].frequency:
                            smallest2 = i
                i += 1
            
            self.nodes[node_count].frequency = self.nodes[smallest1].frequency + self.nodes[smallest2].frequency
            self.nodes[smallest1].parent = node_count - 255
            self.nodes[smallest2].parent = node_count - 255
            self.nodes[node_count].right_child = smallest1
            self.nodes[node_count].left_child = smallest2
            
            node_count += 1

    def decompress(self, src):
        if not src:
            return b''
        
        length = len(src)
        
        remainder = src[0] & 0x0F
        compressed = src[0] >> 7

        if compressed:
            out = bytearray()
            ptr = src[1:]
            
            bit_length = (length - 1) * 8
            if remainder > bit_length:
                 raise ValueError("Invalid huffman data: remainder bits > total bits")
            bit_length -= remainder
            
            bit = 0

            while bit < bit_length:
                mode_bit = (ptr[bit >> 3] >> (bit & 7)) & 1
                bit += 1

                if mode_bit:
                    n = 510
                    while n >= 256:
                        if bit >= bit_length:
                            raise ValueError("Incomplete Huffman code at end of stream")
                        
                        path_bit = (ptr[bit >> 3] >> (bit & 7)) & 1
                        bit += 1
                        
                        n = self.nodes[n].left_child if path_bit == 0 else self.nodes[n].right_child
                    out.append(n)

                else:
                    if bit + 8 > bit_length:
                        break

                    byte_index = bit >> 3
                    bit_in_byte = bit & 7
                    
                    if bit_in_byte == 0:
                        val = ptr[byte_index]
                    else:
                        val = (ptr[byte_index] >> bit_in_byte) | (ptr[byte_index + 1] << (8 - bit_in_byte))
                    
                    out.append(val & 0xFF)
                    bit += 8
            return bytes(out)
        else:
            return src

class Replay:
    def __init__(self, input_stream):
        self.input = input_stream
        self.bytes_seeked = 0

    def get_file_size(self):
        current_pos = self.input.tell()
        self.input.seek(0, 2)
        file_size = self.input.tell()
        self.input.seek(current_pos)
        return file_size

    def decompress_to(self, output_path):
        huffman = Huffman()
        with open(output_path, 'wb') as output:
            self._write_header(output)
            self._write_decompressed_data(output, huffman)

    def _write_header(self, output):
        self.input.seek(0)
        header_data = self.input.read(6)
        output.write(header_data)
        self.bytes_seeked = 6

    def _write_decompressed_data(self, output, huffman):
        file_size = self.get_file_size()
        self.input.seek(self.bytes_seeked)

        while self.bytes_seeked < file_size:
            initial_byte_data = self.input.read(1)
            if not initial_byte_data:
                break
            initial_byte = initial_byte_data[0]
            self.bytes_seeked += 1
            
            message_size = 0
            if initial_byte < 254:
                message_size = initial_byte
            elif initial_byte == 254:
                data = self.input.read(2)
                message_size = unpack('<H', data)[0]
                self.bytes_seeked += 2
            else:
                data = self.input.read(4)
                message_size = unpack('<I', data)[0]
                self.bytes_seeked += 4
            
            if message_size > 0:
                message = self.input.read(message_size)
                self.bytes_seeked += message_size
                
                result = huffman.decompress(message)
                
                len32 = len(result)

                if len32 < 254:
                    output.write(pack('<B', len32))
                elif len32 <= 65535:
                    output.write(pack('<B', 254))
                    output.write(pack('<H', len32))
                else:
                    output.write(pack('<B', 255))
                    output.write(pack('<I', len32))
                
                output.write(result)

def decompress_replay_file(input_path, output_path):
    with open(input_path, 'rb') as f:
        replay = Replay(f)
        replay.decompress_to(output_path)
# endregion

# region Duration Calculation Code
def get_replay_duration(raw_data_path):
    """
    Calculates the total duration of a replay from its raw,
    decompressed data file.
    """
    
    # Constants derived from the C++ source code
    BA_MESSAGE_SESSION_COMMANDS = 1
    SESSION_COMMAND_K_BASE_TIME_STEP = 0

    total_milliseconds = 0

    with open(raw_data_path, 'rb') as f:
        # Skip the 6-byte file header (ID & protocol version)
        f.seek(6)
        
        # Read the stream of top-level messages
        while True:
            # Read the variable-length size of the message chunk
            len_byte_data = f.read(1)
            if not len_byte_data:
                break # End of file
            
            len8 = len_byte_data[0]
            msg_len = 0
            if len8 < 254:
                msg_len = len8
            elif len8 == 254:
                msg_len = unpack('<H', f.read(2))[0]
            else: # 255
                msg_len = unpack('<I', f.read(4))[0]
                
            # Read the message data
            message_data = f.read(msg_len)

            if not message_data: continue

            # We only care about BA_MESSAGE_SESSION_COMMANDS packets
            if message_data[0] == BA_MESSAGE_SESSION_COMMANDS:
                # This message is a container for sub-commands.
                # The first byte is the container ID, so we start parsing at offset 1.
                sub_offset = 1
                while sub_offset < len(message_data):
                    # Read the 2-byte size of the sub-command
                    try:
                        sub_size = unpack('<H', message_data[sub_offset : sub_offset + 2])[0]
                    except error:
                        # Reached a malformed part of the packet; stop parsing this chunk.
                        break
                    
                    # Extract the sub-command data
                    sub_data = message_data[sub_offset + 2 : sub_offset + 2 + sub_size]

                    if not sub_data:
                        # Move to the next sub-command
                        sub_offset += (2 + sub_size)
                        continue

                    # Check if this sub-command is our time-step command
                    if sub_data[0] == SESSION_COMMAND_K_BASE_TIME_STEP:
                        # The second byte of this command is the number of milliseconds
                        num_millis = sub_data[1]
                        total_milliseconds += num_millis
                    
                    # Move to the next sub-command
                    sub_offset += (2 + sub_size)

    duration_seconds = total_milliseconds / 1000.0
    return duration_seconds
# endregion


if __name__ == "__main__":
    from sys import argv, stderr, exit
    if len(argv) < 3:
        print(f"Usage: python {argv[0]} <input_replay_file.brp> <output_raw_file>", file=stderr)
        exit(1)
    input_file = argv[1]
    output_file = argv[2]
    print(f"Decompressing '{input_file}' to '{output_file}'...")
    decompress_replay_file(input_file, output_file)
    print("Calculating replay duration...")
    duration = get_replay_duration(output_file)
    print(f"Replay duration: {duration:.2f} seconds")
