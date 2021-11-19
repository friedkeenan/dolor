"""Contains :class:`types.Chat <.chat.Chat>`."""

import copy
import inspect
import json
import re
import pak

from .string import JSON

from .. import util

class Chat(pak.Type):
    """A :class:`pak.Type` to parse Minecraft "Chat" objects."""

    class Chat:
        """A Minecraft "Chat" object.

        See https://wiki.vg/Chat for more information.

        Parameters
        ----------
        raw_item : ``None`` or :class:`str` or :class:`list` or :class:`dict`
            The raw, unparsed data. First passed to :meth:`prepare_raw_fields`,
            then parsed.
        parent : :class:`Chat.Chat` or ``None``
            The parent of the object.

            If ``None``, then there is no parent.
        **kwargs
            Additional fields to set.

            Key/value pairs are passed to :func:`setattr`.
        """

        # TODO: Handle old style formatting.

        class Field:
            """A field descriptor for a :class:`Chat.Chat`.

            Parameters
            ----------
            default
                The default value of the :class:`~.Field`.
            initial_value
                The initial value to assign the field if not present.

                Its value will be deepcopy'ed on :class:`Chat.Chat` construction.

                .. note::

                    Any :class:`~.Field` which specifies ``initial_value`` should
                    also specify a pack checker.
            field_name : :class:`str` or ``None``
                The name of the :class:`~.Field`.

                This does not have to line up with the name of the
                attribute of the :class:`Chat.Chat` object, but if
                ``field_name`` is ``None``, then it will be the same
                name as the attribute.
            parser : callable or ``None``
                The callable to parse the raw, unparsed item for the :class:`~.Field`.

                See :meth:`parser` for more details.
            pack_checker : callable or ``None``
                The callable to check whether the :class:`~.Field` should be packed.

                See :meth:`pack_checker` for more details.
            packer : callable or ``None``
                The callable to pack the :class:`~.Field`.

                See :meth:`packer` for more details.
            doc : :class:`str` or ``None``
                The docstring for the :class:`~.Field`.

            Raises
            ------
            :exc:`TypeError`
                If both ``default`` and ``initial_value`` are specified, or if
                neither are specified.
            """

            _UNSPECIFIED = util.UniqueSentinel("UNSPECIFIED")

            def __init__(
                self,
                *,
                default       = _UNSPECIFIED,
                initial_value = _UNSPECIFIED,
                field_name    = None,
                parser        = None,
                pack_checker  = None,
                packer        = None,
                doc           = None,
            ):
                if default is not self._UNSPECIFIED and initial_value is not self._UNSPECIFIED:
                    raise TypeError("The 'default' and 'initial_value' parameters are mutually exclusive")

                if default is self._UNSPECIFIED and initial_value is self._UNSPECIFIED:
                    raise TypeError("One of 'default' and 'initial_value' must be specified")

                self.default       = default
                self.initial_value = initial_value

                self.attr_name  = field_name
                self.field_name = field_name

                self._parser       = parser
                self._pack_checker = pack_checker
                self._packer       = packer

                self.__doc__ = doc

            def _new_doc(self, func):
                if self.__doc__ is None:
                    return func.__doc__

                return self.__doc__

            def parser(self, func):
                """A decorator returning a new :class:`~.Field` with the decorated function as its parser.

                The ``__doc__`` attribute of :func: is passed as the ``doc`` parameter for the constructor
                if the :class:`~.Field` does not already have a docstring.

                Parameters
                ----------
                func : callable
                    The callable to parse the raw item.

                    It must take a ``self`` parameter which corresponds to the
                    :class:`Chat.Chat` object, and a ``raw_item`` parameter,
                    corresponding to the raw, unparsed item.

                Returns
                -------
                :class:`~.Field`
                    The resulting :class:`~.Field` with its parser appropriately set.
                """

                return type(self)(
                    default       = self.default,
                    initial_value = self.initial_value,
                    field_name    = self.field_name,
                    parser        = func,
                    pack_checker  = self._pack_checker,
                    packer        = self._packer,
                    doc           = self._new_doc(func),
                )

            def parse(self, instance, raw_item):
                """Parses a raw, unparsed item.

                Parameters
                ----------
                instance : :class:`Chat.Chat`
                    The instance for which parsing is happening.
                raw_item
                    The raw, unparsed item.

                Returns
                -------
                any
                    The parsed value for the :class:`~.Field`.
                """

                if self._parser is None:
                    # Return the raw item unchanged.
                    return raw_item

                return self._parser(instance, raw_item)

            def pack_checker(self, func):
                """A decorator returning a new :class:`~.Field` with the decorated function as its pack checker.

                The ``__doc__`` attribute of :func: is passed as the ``doc`` parameter for
                the constructor if the :class:`~.Field` does not already have a docstring.

                Parameters
                ----------
                func : callable
                    The callable to parse the raw item.

                    It must take a ``self`` parameter which corresponds to the
                    :class:`Chat.Chat` object.

                Returns
                -------
                :class:`~.Field`
                    The resulting :class:`~.Field` with its pack checker appropriately set.
                """

                return type(self)(
                    default       = self.default,
                    initial_value = self.initial_value,
                    field_name    = self.field_name,
                    parser        = self._parser,
                    pack_checker  = func,
                    packer        = self._packer,
                    doc           = self._new_doc(func),
                )

            def should_pack(self, instance):
                """Gets whether a :class:`~.Field` should be packed.

                Parameters
                ----------
                instance : :class:`Chat.Chat`
                    The instance for which packing is happening.

                Returns
                -------
                :class:`bool`
                    Whether the :class:`~.Field` should be packed.
                """

                if self._pack_checker is None:
                    # Only pack the field if it's different from the parent's.

                    value = getattr(instance, self.attr_name)

                    if instance.is_root:
                        return value != self.default

                    return value != getattr(instance.parent, self.attr_name)

                return self._pack_checker(instance)

            def packer(self, func):
                """A decorator returning a new :class:`~.Field` with the decorated function as its packer.

                The ``__doc__`` attribute of :func: is passed as the ``doc`` parameter for
                the constructor if the :class:`~.Field` does not already have a docstring.

                Parameters
                ----------
                func : callable
                    The callable to parse the raw item.

                    It must take a ``self`` parameter which corresponds to the
                    :class:`Chat.Chat` object.

                Returns
                -------
                :class:`~.Field`
                    The resulting :class:`~.Field` with its packer appropriately set.
                """

                return type(self)(
                    default       = self.default,
                    initial_value = self.initial_value,
                    field_name    = self.field_name,
                    parser        = self._parser,
                    pack_checker  = self._pack_checker,
                    packer        = func,
                    doc           = self._new_doc(func),
                )

            def pack(self, instance):
                """Packs the :class:`~.Field` into a raw, unparsed item.

                Parameters
                ----------
                instance : :class:`Chat.Chat`
                    The instance for which packing is happening.

                Returns
                -------
                any
                    The raw, packed item.
                """

                if self._packer is None:
                    # Return the field's value unchanged.
                    return getattr(instance, self.attr_name)

                return self._packer(instance)

            def __set_name__(self, owner, name):
                self.attr_name = name

                if self.field_name is None:
                    self.field_name = name

                self._internal_attr = f"_{name}_chat_field"

            def __repr__(self):
                return f"{type(self).__name__}(field_name={repr(self.field_name)})"

            def __get__(self, instance, owner=None):
                if instance is None:
                    return self

                value = getattr(instance, self._internal_attr, self._UNSPECIFIED)
                if value is self._UNSPECIFIED:
                    if instance.is_root:
                        return self.default

                    return getattr(instance.parent, self.attr_name)

                return value

            def __set__(self, instance, value):
                setattr(instance, self._internal_attr, value)

            def __delete__(self, instance):
                # Try to delete the value specific to the instance.
                # If that fails, simply pass.

                try:
                    delattr(instance, self._internal_attr)
                except AttributeError:
                    pass

        class BooleanField(Field):
            """A helper class for :class:`bool` fields.

            Parameters
            ----------
            parser : callable or ``None``
                The parser for the :class:`~.BooleanField`.

                If unspecified, then a default parser is used.
            packer : callable or ``None``
                The packer for the :class:`~.BooleanField`.

                If unspecified, then a default packer is used.
            **kwargs
                Forwarded onto the parent constructor.
            """

            _BOOL_UNSPECIFIED = util.UniqueSentinel("UNSPECIFIED")

            def __init__(self, *, default=False, parser=_BOOL_UNSPECIFIED, packer=_BOOL_UNSPECIFIED, **kwargs):
                def bool_parser(instance, raw_item):
                    return raw_item == "true"

                def bool_packer(instance):
                    return "true" if getattr(instance, self.attr_name) else "false"

                if parser is self._BOOL_UNSPECIFIED:
                    parser = bool_parser

                if packer is self._BOOL_UNSPECIFIED:
                    packer = bool_packer

                super().__init__(default=default, parser=parser, packer=packer, **kwargs)

            def __set_name__(self, owner, name):
                super().__set_name__(owner, name)

                if self.__doc__ is None:
                    self.__doc__ = f"Whether the text is {self.field_name}."

        bold          = BooleanField()
        italic        = BooleanField()
        underlined    = BooleanField()
        strikethrough = BooleanField()
        obfuscated    = BooleanField()

        color = Field(default=None)

        @color.parser
        def color(self, raw_item):
            """The color of the text."""

            if raw_item == "reset":
                return None

            return raw_item

        @color.packer
        def color(self):
            if self.color is None:
                return "reset"

            return self.color

        insertion = Field(default=None, doc="Text to insert.")

        click_event = Field(default=None, field_name="clickEvent", doc="An event to happen when the text is clicked.")
        hover_event = Field(default=None, field_name="hoverEvent", doc="An event to happen when the text is hovered over.")

        extra = Field(initial_value=[])

        @extra.parser
        def extra(self, raw_item):
            """Extra child components."""

            return [type(self)(raw_child, parent=self) for raw_child in raw_item]

        @extra.pack_checker
        def extra(self):
            return len(self.extra) > 0

        @extra.packer
        def extra(self):
            return [child.as_dict() for child in self.extra]

        text = Field(initial_value=None, doc="The plain text of the object.")

        @text.pack_checker
        def text(self):
            return self.is_string_component

        translate = Field(initial_value=None, doc="The translation key for the text.")

        @translate.pack_checker
        def translate(self):
            return self.is_translation_component

        translate_with = Field(initial_value=[], field_name="with")

        @translate_with.parser
        def translate_with(self, raw_item):
            """The components to translate with."""

            return [type(self)(raw_child, parent=self) for raw_child in raw_item]

        @translate_with.pack_checker
        def translate_with(self):
            return len(self.translate_with) > 0

        @translate_with.packer
        def translate_with(self):
            return [child.as_dict() for child in self.translate_with]

        _translation_strings = {}

        _indexed_format_pattern    = re.compile(r"%(\d)\$[sd]")
        _positional_format_pattern = re.compile(r"%[sd]")

        @classmethod
        def load_translations(cls, translations):
            """Loads translation keys for  use with :meth:`flatten`.

            Parameters
            ----------
            translations : pathlike or :class:`dict` or string file object
                If pathlike, then the file at that path is opened and loaded
                as JSON data.

                If :class:`dict`, then ``translations`` is treated as the loaded
                JSON data of a file.

                If a string file object, then JSON data is loaded from it.
            """

            if util.is_pathlike(translations):
                with open(translations) as f:
                    cls._translation_strings = json.load(f)
            elif isinstance(translations, dict):
                cls._translation_strings = translations
            else:
                cls._translation_strings = json.load(translations)

            for key, value in cls._translation_strings.items():
                # TODO: Do we want stricter formatting types, e.g. putting 's' and 'd' in the format strings?

                value = re.sub(cls._indexed_format_pattern, lambda x: f"{{{int(x.groups()[0]) - 1}}}", value)
                value = re.sub(cls._positional_format_pattern, "{}", value)

                cls._translation_strings[key] = value

        @classmethod
        def fields(cls):
            """Gets the :class:`Fields <.Field>` of the :class:`Chat.Chat` object.

            Returns
            -------
            :class:`list` of :class:`Fields <.Field>`
                The :class:`Fields <.Field>` of the :class:`Chat.Chat` object.
            """

            return [value for _, value in inspect.getmembers(cls, lambda x: isinstance(x, cls.Field))]

        @staticmethod
        def prepare_raw_fields(raw_item):
            """Prepares the raw, unparsed item from the constructor into something usable.

            Parameters
            ----------
            raw_item : ``None`` or :class:`str` of :class:`list` or :class:`dict`
                If ``None``, then an empty :class:`dict` is returned.

                If :class:`str`, then the text of the object.

                If :class:`list`, then several related objects.

                If :class:`dict`, the conventional raw form of the object.
            """

            if raw_item is None:
                return {}

            if isinstance(raw_item, str):
                return {"text": raw_item}

            if isinstance(raw_item, list):
                raw_fields = raw_item[0]

                if "extra" in raw_fields:
                    raw_fields["extra"].extend(raw_item[1:])
                else:
                    raw_fields["extra"] = raw_item[1:]

                return raw_fields

            return raw_item

        def __init__(self, raw_item=None, *, parent=None, **kwargs):
            raw_fields = self.prepare_raw_fields(raw_item)

            self.parent = parent

            for field in self.fields():
                raw_value = raw_fields.get(field.field_name)
                if raw_value is None:
                    if field.initial_value is not field._UNSPECIFIED:
                        setattr(self, field.attr_name, copy.deepcopy(field.initial_value))

                    continue

                setattr(self, field.attr_name, field.parse(self, raw_value))

            for attr_name, attr_value in kwargs.items():
                setattr(self, attr_name, attr_value)

        def as_dict(self):
            """Packs the :class:`Chat.Chat` object into a :class:`dict`.

            This method allows use with :class:`types.StructuredJSON <.StructuredJSON>`
            as well.

            Returns
            -------
            :class:`dict`
                The raw, packed :class:`dict`.
            """

            raw_fields = {}

            for field in self.fields():
                if not field.should_pack(self):
                    continue

                raw_fields[field.field_name] = field.pack(self)

            return raw_fields

        def flatten(self):
            """Flattens the :class:`Chat.Chat` object into a :class:`str`.

            Returns
            -------
            :class:`str`
                The flattened text.
            """

            base_text = ""

            if self.is_string_component:
                base_text = self.text
            elif self.is_translation_component:
                fmt_string = self._translation_strings.get(self.translate)

                if fmt_string is None:
                    base_text = self.translate
                else:
                    base_text = fmt_string.format(*(child.flatten() for child in self.translate_with))

            return base_text + "".join(child.flatten() for child in self.extra)

        def __eq__(self, other):
            if not isinstance(other, type(self)):
                other = type(self)(other)

            return self.as_dict() == other.as_dict()

        def __str__(self):
            return self.flatten()

        def __repr__(self):
            return f"{type(self).__name__}({self.as_dict()})"

        @property
        def is_root(self):
            """Whether the :class:`Chat.Chat` object is the root object."""

            return self.parent is None

        @property
        def is_string_component(self):
            """Whether the :class:`Chat.Chat` object is a string component."""

            return self.text is not None

        @property
        def is_translation_component(self):
            """Whether the :class:`Chat.Chat` object is a translation component."""

            return self.translate is not None

    _default = Chat("")

    def __set__(self, instance, value):
        if not isinstance(value, self.Chat):
            value = self.Chat(value)

        super().__set__(instance, value)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.Chat(JSON.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return JSON.pack(value.as_dict(), ctx=ctx)
