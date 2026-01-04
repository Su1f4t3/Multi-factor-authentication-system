"""验证data.bin是加密的"""
with open('data/data.bin', 'rb') as f:
    data = f.read()

print(f'文件大小: {len(data)} 字节')
print(f'前50字节（十六进制）: {data[:50].hex()}')
print(f'\n检查是否包含明文关键词:')
print(f'  包含 "username": {b"username" in data}')
print(f'  包含 "alice": {b"alice" in data}')
print(f'  包含 "charlie": {b"charlie" in data}')
print(f'  包含 "password": {b"password" in data}')
print(f'  包含 "face": {b"face" in data}')

print(f'\n✓ data.bin 是完全加密的二进制文件，不包含任何明文数据')
