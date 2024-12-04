from sys import argv
from os import path
import charset_normalizer

class MSD:
    def __init__(self, file_path: str):
        self.name = path.basename(file_path)
        self.error = None

        if not path.exists(file_path):
            self.error = 'file does not exist'
            return
        
        with open(file_path, 'rb') as file:
            self.bytes = file.read()

        if not MSD.check_header(self.bytes):
            self.error = 'invalid msd header'

        self.get_encoding()
        self.extract_texts()

    def read(self, addr: int, size: int):
        return int.from_bytes(self.bytes[addr : addr+size], 'little')

    def read_string(self, addr: int, stop_pattern: bytes, encoding: str = None):
        stop = self.bytes.find(stop_pattern, addr)
        if stop == -1:
            stop = len(self.bytes)

        content = self.bytes[addr : stop]
        return content.decode(encoding) if encoding is not None else content

    def extract_texts(self):
        self.texts: dict[int, str] = {}
        text_amount = self.read(8, 4)

        for i in range(text_amount):
            text_id = self.read(0x10 + i * 0xC, 4)
            addr = self.read(0x18 + i * 0xC, 4)
            self.texts[text_id] = self.read_string(addr, b'\x00\x00', self.encoding)

    def get_encoding(self):
        first_text_addr = self.read(0x18, 4)
        result = charset_normalizer.detect(self.read_string(first_text_addr, b'\x00\x00'))
        fake_encoding = result['encoding'].lower()

        if fake_encoding in ('cp932', 'shift-jis'):
            self.encoding = 'shift-jis'
        else:
            self.encoding = 'ansi'

    def check_header(content: bytearray):
        return content[0 : 8] == b'MSDA\x00\x00\x01\x00'

def main():
    if len(argv) < 2:
        print('Usage: <script.py> <file1.msd> [<file2.msd ...]')
        return
    
    for arg in argv[1:]:
        msd = MSD(arg)

        if msd.error is not None:
            print(f'Error with {msd.name}: {msd.error}')
            continue
        
        with open(argv[1] + '.txt', 'w', encoding=msd.encoding) as file:
            for text_id, text in msd.texts.items():
                file.write(f'{hex(text_id)}: "{text.replace('\n', '\\n')}"\n')
        
        print(f'{msd.name} read successfully')

if __name__ == '__main__':
    main()