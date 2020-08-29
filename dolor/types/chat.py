import json
import re

from . import Type, Json

class Chat(Type):
    class Chat:
        pos_pattern = re.compile(r"%(\d)\$[sd]")
        general_pattern = re.compile(r"%[sd]")
        translate_fmt = {}

        @classmethod
        def load_translations(cls, file):
            if isinstance(file, str):
                with open(file) as f:
                    cls.translate_fmt = json.load(f)
            else:
                cls.translate_fmt = json.load(file)

            for key, value in cls.translate_fmt.items():
                value = re.sub(cls.pos_pattern, lambda x: "{" + str(int(x.groups()[0]) - 1) + "}", value)
                value = re.sub(cls.general_pattern, r"{}", value)

                cls.translate_fmt[key] = value

        def __init__(self, raw, parent=None):
            self.parent = parent
            if parent is None:
                self.bold = False
                self.italic = False
                self.underlined = False
                self.strikethrough = False
                self.obfuscated = False
                self.color = None
                self.insertion = None
                self.click_event = None
                self.hover_event = None

            self.extra = []

            if isinstance(raw, list):
                raw = raw[0]

                if "extra" in raw:
                    raw["extra"] += raw[1:]
                else:
                    raw["extra"] = raw[1:]

            if not isinstance(raw, dict):
                raw = {"text": raw}

            bold = raw.get("bold")
            if bold is not None:
                self.bold = True if bold == "true" else False

            italic = raw.get("italic")
            if italic is not None:
                self.italic = True if italic == "true" else False

            underlined = raw.get("underlined")
            if underlined is not None:
                self.underlined = True if underlined == "true" else False

            strikethrough = raw.get("strikethrough")
            if strikethrough is not None:
                self.strikethrough = True if strikethrough == "true" else False

            obfuscated = raw.get("obfuscated")
            if obfuscated is not None:
                self.obfuscated = True if obfuscated == "true" else False

            color = raw.get("color")
            if color is not None:
                self.color = color

            insertion = raw.get("insertion")
            if insertion is not None:
                self.insertion = type(self)(insertion)

            click_event = raw.get("clickEvent")
            if click_event is not None:
                self.click_event = click_event

            hover_event = raw.get("hoverEvent")
            if hover_event is not None:
                self.hover_event = hover_event

            extra = raw.get("extra")
            if extra is not None:
                self.extra = [type(self)(x, self) for x in extra]

            self.text = None
            self.translate = None

            text = raw.get("text")
            translate = raw.get("translate")

            if text is not None:
                self.text = text # TODO: Parse old style formatting
            elif translate is not None:
                self.translate = translate

                tr_with = raw.get("with")
                if tr_with is not None:
                    self.tr_with = [type(self)(x, self) for x in tr_with]
                else:
                    self.tr_with = []
            else:
                # TODO: support more component types
                raise ValueError("Invalid component type")

        def __getattr__(self, attr):
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

        def to_dict(self):
            ret = {}

            if (self.parent is None and self.bold) or (self.parent is not None and self.parent.bold != self.bold):
                ret["bold"] = "true" if self.bold else "false"

            if (self.parent is None and self.italic) or (self.parent is not None and self.parent.italic != self.italic):
                ret["italic"] = "true" if self.italic else "false"

            if (self.parent is None and self.underlined) or (self.parent is not None and self.parent.underlined != self.underlined):
                ret["underlined"] = "true" if self.underlined else "false"

            if (self.parent is None and self.strikethrough) or (self.parent is not None and self.parent.strikethrough != self.strikethrough):
                ret["strikethrough"] = "true" if self.strikethrough else "false"

            if (self.parent is None and self.obfuscated) or (self.parent is not None and self.parent.obfuscated != self.obfuscated):
                ret["obfuscated"] = "true" if self.obfuscated else "false"

            if (self.parent is None and self.color is not None) or (self.parent is not None and self.parent.color != self.color and self.color is not None):
                ret["color"] = self.color

            if (self.parent is None and self.insertion is not None) or (self.parent is not None and self.parent.insertion != self.insertion and self.insertion is not None):
                ret["insertion"] = self.insertion.to_dict()

            if (self.parent is None and self.click_event is not None) or (self.parent is not None and self.parent.click_event != self.click_event and self.click_event is not None):
                ret["clickEvent"] = self.click_event

            if (self.parent is None and self.hover_event is not None) or (self.parent is not None and self.parent.hover_event != self.hover_event and self.hover_event is not None):
                ret["hoverEvent"] = self.hover_event

            if len(self.extra) != 0:
                ret["extra"] = [x.to_dict() for x in self.extra]

            if self.is_string:
                ret["text"] = self.text
            elif self.is_translate:
                ret["translate"] = self.translate

                if len(self.tr_with) != 0:
                    ret["with"] = [x.to_dict() for x in self.tr_with]

            return ret

        def __repr__(self):
            return f"{type(self).__name__}({self.to_dict()})"

    def unpack(self, buf):
        return self.Chat(Json(buf).value)

    def __bytes__(self):
        return bytes(Json(self.value.to_dict()))
