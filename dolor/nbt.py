"""NBT marshaling.

See https://wiki.vg/NBT for a specification of the format.
"""

import abc
import io
import struct
import gzip
import inspect

from . import util
from . import types

class Tag(abc.ABC):
    """An NBT tag.

    :meta no-undoc-members:

    Parameters
    ----------
    value : any, optional
        The tag's value. If unspecified, then the default value will be used.
    root_name : :class:`str`, optional
        The root name of the tag. If specified, then the tag will be treated
        as a root tag.

    Attributes
    ----------
    id : :class:`int` or ``None``
        The tag's id. If ``None``, then the tag will not be used in marshaling.
    type : subclass of :class:`~.Type`
        The tag's underlying type. Used to automatically pack and unpack
        the raw data of the tag. Must be able to be used without a specified
        :class:`~.TypeContext`.
    value : any
        The tag's value.
    root_name : :class:`str` or ``None``
        The tag's root name. If not ``None``, then the tag will be treated
        as a root tag.
    """

    id   = None
    type = None

    @classmethod
    def from_id(cls, id):
        """Gets the tag whose id is `id`.

        Will search through the subclasses of :class:`Tag`,
        ignoring subclasses whose :attr:`id` attribute is ``None``.

        Parameters
        ----------
        id : :class:`int`
            The id to look for.

        Returns
        -------
        subclass of :class:`Tag`
            The tag whose id is ``id``.

        Examples
        --------
        >>> import dolor
        >>> dolor.nbt.Tag.from_id(0)
        <class 'dolor.nbt.End'>
        """

        for tag in util.get_subclasses(cls):
            if tag.id is not None and tag.id == id:
                return tag

        return None

    def __init__(self, value=None, *, root_name=None):
        if value is None:
            value = self.type.default()

        self.value     = value
        self.root_name = root_name

    def pack(self):
        """Packs the tag.

        Does not include the id. Use :func:`dump` for a complete dump.

        Returns
        -------
        :class:`bytes`
            The packed tag.
        """

        if self.root_name is not None:
            return String(self.root_name).pack() + self._pack(self.value)

        return self._pack(self.value)

    def __repr__(self):
        ret = f"{type(self).__name__}("

        if self.root_name is not None:
            ret += f"root_name={repr(self.root_name)}, "

        return ret + f"{repr(self.value)})"

    @classmethod
    def unpack(cls, buf, *, root=False):
        """Unpacks a buffer into a tag.

        Does not include the id. Use :func:`load` to properly
        unpack NBT data.

        Parameters
        ----------
        buf : file object or :class:`bytes` or :class:`bytearray`
            The buffer to unpack.
        root : :class:`bool`, optional
            Whether the tag is a root tag.

        Returns
        -------
        :class:`Tag`
            The unpacked tag.
        """

        buf = util.file_object(buf)

        if root:
            root_name = String.unpack(buf).value
        else:
            root_name = None

        ret = cls._unpack(buf)

        ret.root_name = root_name

        return ret

    @classmethod
    def _unpack(cls, buf):
        return cls(cls.type.unpack(buf))

    @classmethod
    def _pack(cls, value):
        return cls.type.pack(value)

class End(Tag):
    id   = 0
    type = types.EmptyType

class Byte(Tag):
    id   = 1
    type = types.Byte

class Short(Tag):
    id   = 2
    type = types.Short

class Int(Tag):
    id   = 3
    type = types.Int

class Long(Tag):
    id   = 4
    type = types.Long

class Float(Tag):
    id   = 5
    type = types.Float

class Double(Tag):
    id   = 6
    type = types.Double

class ByteArray(Tag):
    id   = 7
    type = types.Byte[types.Int]

class String(Tag):
    id = 8

    # Would be nicer to use Java's wack modified utf-8 but ew
    type = types.String(prefix=types.UnsignedShort, max_length=0xffff)

class List(Tag):
    """A List tag.

    Parameters
    ----------
    tag_or_value : subclass of :class:`Tag` or :class:`list`
        If a subclass of :class:`Tag`, then a new subclass of :class:`List`
        will be generated with its :attr:`tag` attribute set to ``tag_or_value``.

        Otherwise, :meth:`__init__` will continue on as normal.
    *args, **kwargs
        Forwarded to :meth:`__init__`.

    Attributes
    ----------
    tag : subclass of :class:`Tag`
        The tag of the values of this :class:`List`.
    value : :class:`list`
        A list of values for :attr:`tag`.
    """

    id = 9

    tag = None

    def __new__(cls, tag_or_value=None, *args, **kwargs):
        if not isinstance(tag_or_value, type):
            if cls.tag is None:
                raise TypeError(f"Use of {cls.__name__} without setting its tag")

            return super().__new__(cls)

        return type(f"{cls.__name__}({tag_or_value.__name__})", (cls,), dict(
            tag = tag_or_value,
        ))

    def __init__(self, value=None, *, root_name=None):
        if value is None:
            value = []

        self.value     = value
        self.root_name = root_name

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, value):
        self.value[index] = value

    def __delitem__(self, index):
        del self.value[index]

    @classmethod
    def _unpack(cls, buf):
        id  = types.UnsignedByte.unpack(buf)
        tag = Tag.from_id(id)

        new_cls = cls(tag)

        size = Int.unpack(buf).value

        return new_cls([tag.unpack(buf).value for x in range(size)])

    @classmethod
    def _pack(cls, value):
        return types.UnsignedByte.pack(cls.tag.id) + Int(len(value)).pack() + b"".join(cls.tag(x).pack() for x in value)

class Compound(Tag):
    """A Compound tag.

    Attributes
    ----------
    value : :class:`dict`
        A dictionary whose keys are :class:`str` objects
        and whose values are :class:`Tag` objects.
    """

    id = 10

    def __init__(self, value=None, *, root_name=None):
        if value is None:
            value = {}

        self.value     = value
        self.root_name = root_name

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __delitem__(self, key):
        del self.value[key]

    @classmethod
    def _unpack(cls, buf):
        fields = {}

        while True:
            id  = types.UnsignedByte.unpack(buf)
            tag = Tag.from_id(id)

            if tag == End:
                return cls(fields)

            name  = String.unpack(buf).value
            value = tag.unpack(buf)

            fields[name] = value

    @classmethod
    def _pack(cls, value):
        return b"".join(types.UnsignedByte.pack(y.id) + String(x).pack() + y.pack() for x, y in value.items()) + types.UnsignedByte.pack(End.id)

class IntArray(Tag):
    id   = 11
    type = types.Int[types.Int]

class LongArray(Tag):
    id   = 12
    type = types.Long[types.Int]

def load(f):
    r"""Loads a complete NBT dump into a :class:`Tag`.

    Parameters
    ----------
    f : pathlike or :class:`bytes` or :class:`bytearray` or file object
        If a pathlike, then the path to the file to read from.
        Otherwise the data to load.

        The data may be uncompressed, gzip'd, or zlib'd.

    Returns
    -------
    :class:`Tag`
        The loaded tag.

    Examples
    --------
    >>> import dolor
    >>> dolor.nbt.load(b"\x08\x00\x04test\x00\x0eThis is a test")
    String(root_name='test', 'This is a test')
    """

    should_close = False

    if util.is_pathlike(f):
        f = open(f, "rb")
        should_close = True
    else:
        f = util.file_object(f)

    magic = f.read(2)
    f.seek(-2, 1)

    # Quick and dirty magic checking, I'm sorry
    if magic == b"\x1f\x8b":
        f = gzip.GzipFile(fileobj=f)
    elif magic in (b"\x78\x01", b"\x78\x5e", b"\x78\x9c", b"\x78\xda"):
        f = util.ZlibDecompressFile(f)

    id  = types.UnsignedByte.unpack(f)
    tag = Tag.from_id(id)

    ret = tag.unpack(f, root=True)

    if should_close:
        f.close()

    return ret

def dump(obj, f=None, *, compression=None):
    r"""Dumps a root tag into a binary dump.

    Parameters
    ----------
    obj : :class:`Tag`
        The root tag to dump.
    f : file object, optional
        The file object to dump to. If unspecified, the dumped
        data will instead be returned.
    compression : :class:`function` or any, optional
        The compression used to compress the dumped data. If unspecified,
        the data won't be compressed.

        If a :class:`function`, then the data will be passed to it and
        the return value will be treated as the new, compressed data.

        Otherwise, the :attr:`compress` attribute of `compression` will
        be used as the compression function, allowing you to pass a
        module like :mod:`gzip` as `compression`.

    Returns
    -------
    :class:`bytes` or :class:`int`
        If ``f`` is unspecified, then :class:`bytes` will be returned.
        Otherwise how many bytes were written to ``f`` will be returned.

    Raises
    ------
    :exc:`ValueError`
        If ``obj`` is not a root tag.

    Examples
    --------
    >>> import dolor
    >>> import gzip
    >>> import io
    >>> tag = dolor.nbt.String("This is a test", root_name="test")
    >>> dolor.nbt.dump(tag)
    b'\x08\x00\x04test\x00\x0eThis is a test'
    >>> dolor.nbt.dump(tag, compression=gzip) # doctest: +SKIP
    b'\x1f\x8b\x08\x00u;\xfa_\x02\xff\xe3``)I-.a\xe0\x0b\xc9\xc8,V\x00\xa2D\x05\x10\x1f\x00(\x9a)|\x17\x00\x00\x00'
    >>> f = io.BytesIO()
    >>> dolor.nbt.dump(tag, f)
    23
    >>> f.getvalue()
    b'\x08\x00\x04test\x00\x0eThis is a test'
    """

    if obj.root_name is None:
        raise ValueError("Cannot dump a non-root tag.")

    if compression is not None and not inspect.isfunction(compression):
        compression = compression.compress

    data = types.UnsignedByte.pack(obj.id) + obj.pack()

    if compression is not None:
        data = compression(data)

    if f is None:
        return data

    return f.write(data)
