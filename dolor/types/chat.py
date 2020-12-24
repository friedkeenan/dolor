import json
import re

from .. import util
from .type import Type
from .string import Json

class Chat(Type):
    class Chat:
        # TODO: Figure out a clean way to not use regex?
        pos_pattern     = re.compile(r"%(\d)\$[sd]")
        general_pattern = re.compile(r"%[sd]")

        translate_fmt = {}

        @classmethod
        def load_translations(cls, file):
            if util.is_pathlike(file):
                with open(file) as f:
                    cls.translate_fmt = json.load(f)
            else:
                cls.translate_fmt = json.load(file)

            for key, value in cls.translate_fmt.items():
                value = re.sub(cls.pos_pattern, lambda x: f"{{{int(x.groups()[0]) - 1}}}", value)
                value = re.sub(cls.general_pattern, r"{}", value)

                cls.translate_fmt[key] = value

        def __init__(self, raw, parent=None):
            self.parent = parent
            if parent is None:
                self.bold          = False
                self.italic        = False
                self.underlined    = False
                self.strikethrough = False
                self.obfuscated    = False

                self.color       = None
                self.insertion   = None
                self.click_event = None
                self.hover_event = None

            self.extra = []

            raw = self.handle_type(raw)

            bool_handler     = lambda x: (x == "true")
            children_handler = lambda children: [type(self)(x, self) for x in children]

            self.parse_field(raw, "bold",          bool_handler)
            self.parse_field(raw, "italic",        bool_handler)
            self.parse_field(raw, "underlined",    bool_handler)
            self.parse_field(raw, "strikethrough", bool_handler)
            self.parse_field(raw, "obfuscated",    bool_handler)

            self.parse_field(raw, "color")
            self.parse_field(raw, "insertion")
            self.parse_field(raw, "click_event", key="clickEvent")
            self.parse_field(raw, "hover_event", key="hoverEvent")

            self.parse_field(raw, "extra", children_handler)

            self.text      = None
            self.translate = None

            if self.parse_field(raw, "text"):
                # TODO: Parse old style formatting
                pass
            elif self.parse_field(raw, "translate"):
                if not self.parse_field(raw, "tr_with", children_handler, key="with"):
                    self.tr_with = []
            else:
                # TODO: Support more component types
                raise ValueError("Invalid component type")

        def handle_type(self, raw):
            if raw is None:
                return {"text": "None"}

            if isinstance(raw, list):
                ret = raw[0]

                if "extra" in ret:
                    ret["extra"].extend(raw[1:])
                else:
                    ret["extra"] = raw[1:]

                return ret

            if isinstance(raw, str):
                return {"text": raw}

            return raw

        def parse_field(self, raw, attr, handler=None, *, key=None):
            if key is None:
                key = attr

            field = raw.get(key)
            if field is not None:
                if handler is None:
                    setattr(self, attr, field)
                else:
                    setattr(self, attr, handler(field))

                return True

            return False

        def pack_field(self, raw, attr, handler=None, *, key=None):
            if key is None:
                key = attr

            field = getattr(self, attr)

            if (self.parent is None and field) or (self.parent is not None and getattr(self.parent, attr) != field and field is not None):
                if handler is None:
                    raw[key] = field
                else:
                    raw[key] = handler(field)

                return True

            return False

        def __getattr__(self, attr):
            # Use __getattribute__ here to avoid infinite recursion
            # if self.parent is not set (i.e. in deepcopy's) and so
            # it will raise an AttributeError in said case.
            if self.__getattribute__("parent") is None:
                raise AttributeError

            return getattr(self.parent, attr)

        @property
        def is_string(self):
            return self.text is not None

        @property
        def is_translate(self):
            return self.translate is not None

        def flatten(self):
            base = ""

            if self.is_string:
                base = self.text
            elif self.is_translate:
                fmt = self.translate_fmt.get(self.translate)

                if fmt is None:
                    base = self.translate
                else:
                    base = fmt.format(*(x.flatten() for x in self.tr_with))

            return base + "".join(x.flatten() for x in self.extra)

        def dict(self):
            bool_handler = lambda x: ("true" if x else "false")

            def children_handler(children):
                ret = []

                for c in children:
                    data = c.dict()

                    # If a child only has a "text" field, then
                    # it can be turned into just a string
                    if "text" in data and len(data) == 1:
                        ret.append(data["text"])
                    else:
                        ret.append(data)

                return ret

            ret = {}

            self.pack_field(ret, "bold",          bool_handler)
            self.pack_field(ret, "italic",        bool_handler)
            self.pack_field(ret, "underlined",    bool_handler)
            self.pack_field(ret, "strikethrough", bool_handler)
            self.pack_field(ret, "obfuscated",    bool_handler)

            self.pack_field(ret, "color")
            self.pack_field(ret, "insertion")
            self.pack_field(ret, "click_event", key="clickEvent")
            self.pack_field(ret, "hover_event", key="hoverEvent")

            if len(self.extra) > 0:
                self.pack_field(ret, "extra", children_handler)

            if self.is_string:
                ret["text"] = self.text
            elif self.is_translate:
                ret["translate"] = self.translate

                if len(self.tr_with) > 0:
                    self.pack_field(ret, "tr_with", children_handler, key="with")

            return ret

        def __eq__(self, other):
            return self.dict() == other.dict()

        def __str__(self):
            return self.flatten()

        def __repr__(self):
            return f"{type(self).__name__}({self.dict()})"

    _default = Chat("")

    def __set__(self, instance, value):
        if not isinstance(value, self.Chat):
            value = self.Chat(value)

        super().__set__(instance, value)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.Chat(Json.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return Json.pack(value.dict(), ctx=ctx)
