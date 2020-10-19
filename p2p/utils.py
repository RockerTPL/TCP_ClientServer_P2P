
data_unit = 512

def encode_str(string, max_len):
    """
    encode a string to length of max_len
    """
    string += '$'
    res = string.encode('ascii')
    str_len = len(string)
    assert str_len <= max_len
    for i in range(max_len - str_len):
        res += b'\0'
    return res


def decode_str(data):
    """
    decode a string encoded by encode_str
    """
    string = data.decode('ascii').split('$')
    return string[0]


def recvall(soc, length):
    """
    receive a fixed length of data
    """
    data = b''
    while len(data) < length:
        data += soc.recv(length - len(data))
    return data
