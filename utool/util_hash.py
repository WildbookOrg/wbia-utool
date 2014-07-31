from __future__ import absolute_import, division, print_function
import hashlib
import six
import uuid
from .util_inject import inject
print, print_, printDBG, rrr, profile = inject(__name__, '[hash]')

# default length of hash codes
HASH_LEN = 16

# A large base-54 alphabet (all chars are valid for filenames but not # pretty)
ALPHABET_54 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
               'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
               'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
               'u', 'v', 'w', 'x', 'y', 'z', ';', '=', '@', '[',
               ']', '^', '_', '`', '{', '}', '~', '!', '#', '$',
               '%', '&', '+', ',']


# A large base-41 alphabet (prettier subset of base 54)
ALPHABET_41 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
               'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
               'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
               'u', 'v', 'w', 'x', 'y', 'z', '@', '!', '%', '&',
               '+']


ALPHABET = ALPHABET_41
BIGBASE = len(ALPHABET)


def hashstr_arr(arr, lbl='arr', **kwargs):
    """ <CYTH> """
    if isinstance(arr, list):
        arr = tuple(arr)  # force arrays into a tuple
    if isinstance(arr, tuple):
        arr_shape = '(' + str(len(arr)) + ')'
    else:
        arr_shape = str(arr.shape).replace(' ', '')
    arr_hash = hashstr(arr, **kwargs)
    arr_uid = ''.join([lbl, '(', arr_shape, arr_hash, ')'])
    return arr_uid


def hashstr(data, hashlen=HASH_LEN):
    """ <CYTH> """
    if isinstance(data, tuple):
        data = repr(data)
    if six.PY3:
        data = data.encode('utf-8')
    # Get a 128 character hex string
    hashstr = hashlib.sha512(data).hexdigest()
    #if six.PY3:
    # Shorten length of string (by increasing base)
    hashstr2 = convert_hexstr_to_bigbase(hashstr)
    # Truncate
    hashstr = hashstr2[:hashlen]
    return hashstr

"""
def valid_filename_ascii_chars():
    # Find invalid chars
    ntfs_inval = '< > : " / \ | ? *'.split(' ')
    other_inval = [' ', '\'', '.']
    #case_inval = map(chr, range(97, 123))
    case_inval = map(chr, range(65, 91))
    invalid_chars = set(ntfs_inval + other_inval + case_inval)
    # Find valid chars
    valid_chars = []
    for index in range(32, 127):
        char = chr(index)
        if not char in invalid_chars:
            print index, chr(index)
            valid_chars.append(chr(index))
    return valid_chars
valid_filename_ascii_chars()
"""


def convert_hexstr_to_bigbase(hexstr):
    """ Packs a long hexstr into a shorter length string with a larger base
    <CYTH> """
    x = int(hexstr, 16)  # first convert to base 16
    if x == 0:
        return '0'
    sign = 1 if x > 0 else -1
    x *= sign
    digits = []
    while x:
        digits.append(ALPHABET[x % BIGBASE])
        x //= BIGBASE
    if sign < 0:
        digits.append('-')
        digits.reverse()
    newbase_str = ''.join(digits)
    return newbase_str


def hashstr_md5(data):
    hashstr = hashlib.md5(data).hexdigest()
    #bin(int(my_hexdata, scale))
    return hashstr


def hashstr_sha1(data, base10=False):
    """ <CYTH> """
    hashstr = hashlib.sha1(data).hexdigest()
    if base10:
        hashstr = int("0x" + hashstr, 0)
    return hashstr


def get_file_hash(fpath, blocksize=65536, hasher=None):
    """
    http://stackoverflow.com/questions/3431825/generating-a-md5-checksum-of-a-file
    http://stackoverflow.com/questions/5001893/when-should-i-use-sha-1-and-when-should-i-use-sha-2
    """
    if hasher is None:
        hasher = hashlib.sha1()
    with open(fpath, 'rb') as file_:
        buf = file_.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file_.read(blocksize)
        return hasher.digest()


def get_file_uuid(fpath, hasher=None):
    """ Creates a uuid from the hash of a file
    <CYTH>
    """
    if hasher is None:
        hasher = hashlib.sha1()  # 20 bytes of output
        #hasher = hashlib.sha256()  # 32 bytes of output
    # sha1 produces a 20 byte hash
    hashbytes_20 = get_file_hash(fpath, hasher=hasher)
    # sha1 produces 20 bytes, but UUID requires 16 bytes
    hashbytes_16 = hashbytes_20[0:16]
    uuid_ = uuid.UUID(bytes=hashbytes_16)
    return uuid_


def image_uuid(pil_img):
    """ UNSAFE: DEPRICATE: JPEG IS NOT GAURENTEED TO PRODUCE CONSITENT VALUES ON
    MULTIPLE MACHINES image global unique id
    http://stackoverflow.com/questions/23565889/jpeg-images-have-different-pixel-values-across-multiple-devices
    """
    # Get the bytes of the image
    img_bytes_ = pil_img.tobytes()
    uuid_ = hashable_to_uuid(img_bytes_)
    return uuid_


def augment_uuid(uuid_, *hashables):
    """ <CYTH> """
    #from six.moves import reprlib
    #uuidhex_data   = uuid_.get_bytes()
    uuidhex_data   = uuid_.bytes
    #hashable_str    = ''.join(map(repr, hashables))
    # Python 2 and 3 diverge here because repr returns
    # ascii data in python2 and unicode text in python3
    # it would be nice to
    if six.PY2:
        hashable_text = ''.join(map(repr, hashables))
        hashable_data = hashable_text.encode('utf-8')
        #hashable_data = b''.join(map(bytes, hashables))
    elif six.PY3:
        hashable_text    = ''.join(map(repr, hashables))
        hashable_data = hashable_text.encode('utf-8')
        #hashable_data = b''.join(map(bytes, hashables))
    augmented_data   = uuidhex_data + hashable_data
    augmented_uuid_ = hashable_to_uuid(augmented_data)
    return augmented_uuid_


def hashable_to_uuid(hashable_):
    """ <CYTH>
    hashables are bytes-like objects
       An object that supports the Buffer Protocol, like bytes, bytearray or
       memoryview. Bytes-like objects can be used for various operations that
       expect binary data, such as compression, saving to a binary file or
       sending over a socket. Some operations need the binary data to be
       mutable, in which case not all bytes-like objects can apply.
    """
    # Hash the bytes
    try:
        #print('hashable_=%r' % (hashable_,))
        if six.PY3:
            # If hashable_ is text (python3)
            if isinstance(hashable_, bytes):
                bytes_ = hashable_
            if isinstance(hashable_, str):
                bytes_ = hashable_.encode('utf-8')
                #print('sbytes=%r' % (bytes_,))
            else:
                #bytes_ = bytearray(hashable_)
                bytes_ = bytes(hashable_)
                #bytes_ = repr(hashable_).encode('utf-8')
                #print('bbytes=%r' % (bytes_,))
        elif six.PY2:
            # If hashable_ is data (python2)
            if isinstance(hashable_, bytes):
                bytes_ = hashable_
            elif isinstance(hashable_, str):
                bytes_ = hashable_.encode('utf-8')
            #print('bytes=%r' % (bytes_,))
        bytes_sha1 = hashlib.sha1(bytes_)
    except Exception as ex:
        import utool
        utool.printex(ex, key_list=[(type, 'bytes_')])
        raise
    # Digest them into a hash
    #hashstr_40 = img_bytes_sha1.hexdigest()
    #hashstr_32 = hashstr_40[0:32]
    hashbytes_20 = bytes_sha1.digest()
    hashbytes_16 = hashbytes_20[0:16]
    uuid_ = uuid.UUID(bytes=hashbytes_16)
    return uuid_


def deterministic_uuid(hashable):
    """ <CYTH> """
    return hashable_to_uuid(hashable)


def random_uuid():
    """ <CYTH> """
    return uuid.uuid4()


def get_zero_uuid():
    return uuid.UUID('00000000-0000-0000-0000-000000000000')

# Cleanup namespace
del ALPHABET_41
del ALPHABET_54
