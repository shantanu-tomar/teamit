from Cryptodome import Random
from Cryptodome.Cipher import AES
import base64
from hashlib import md5

BLOCK_SIZE = 16

def pad(data, block_size):
    length = block_size - (len(data) % block_size)
    return data + (chr(length)*length).encode()

def unpad(data, block_size):
    return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]

def bytes_to_key(data, salt, output=48):
    # extended from https://gist.github.com/gsakkis/4546068
    assert len(salt) == 8, len(salt)
    data += salt
    key = md5(data).digest()
    final_key = key
    while len(final_key) < output:
        key = md5(key + data).digest()
        final_key += key
    return final_key[:output]

def encrypt(message, passphrase, block_size=None):
    salt = Random.new().read(8)

    if block_size is None:
        block_size = BLOCK_SIZE

    key_iv = bytes_to_key(passphrase, salt, 32+block_size)
    key = key_iv[:32]
    iv = key_iv[32:]
    aes = AES.new(key, AES.MODE_CBC, iv)
    return base64.urlsafe_b64encode(b"Salted__" + salt + aes.encrypt(pad(message, block_size)))

def decrypt(encrypted, passphrase, block_size=None):
    if block_size is None:
        block_size = BLOCK_SIZE

    encrypted = base64.urlsafe_b64decode(encrypted)
    assert encrypted[0:8] == b"Salted__"
    salt = encrypted[8:block_size]
    key_iv = bytes_to_key(passphrase, salt, 32+block_size)
    key = key_iv[:32]
    iv = key_iv[32:]
    aes = AES.new(key, AES.MODE_CBC, iv)
    return unpad(aes.decrypt(encrypted[block_size:]), block_size)
