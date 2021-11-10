from dolor import *

from ..util import assert_type_marshal_func

def test_chat_parsing():
    chat = types.Chat.Chat("test")
    assert chat.text == "test"

    chat = types.Chat.Chat([{"text": "test", "bold": "true"}, "child"])
    assert chat.text == "test"
    assert chat.bold
    assert chat.extra[0].text == "child"
    assert chat.extra[0].bold

    chat = types.Chat.Chat({
        "text": "test",
        "bold": "true",
    })

    assert chat.text == "test"
    assert chat.bold

def test_chat_defaults():
    chat = types.Chat.Chat("")

    assert not chat.bold
    assert not chat.italic
    assert not chat.underlined
    assert not chat.strikethrough
    assert not chat.obfuscated

    assert chat.color     is None
    assert chat.insertion is None

    assert chat.click_event is None
    assert chat.hover_event is None

    assert chat.extra == []

    # Make sure each 'extra' list is different.
    assert chat.extra is not types.Chat.Chat("").extra

    assert chat.translate is None
    assert chat.translate_with == []
    assert chat.translate_with is not types.Chat.Chat("").translate_with

def test_chat_packing():
    chat = types.Chat.Chat("test")

    assert chat.as_dict() == {"text": "test"}

    chat.bold = True
    assert chat.as_dict() == {"text": "test", "bold": "true"}

    chat.extra.append(types.Chat.Chat("child", bold=True, parent=chat))

    assert chat.as_dict() == {
        "text": "test",
        "bold": "true",
        "extra": [
            {"text": "child"},
        ]
    }

    chat.extra[0].bold = False

    assert chat.as_dict() == {
        "text": "test",
        "bold": "true",
        "extra": [
            {
                "text": "child",
                "bold": "false",
            },
        ]
    }

def test_chat_flattening():
    chat = types.Chat.Chat("test")

    assert chat.flatten() == "test"

    chat.extra.append(types.Chat.Chat("child", parent=chat))
    assert chat.flatten() == "testchild"

    chat = types.Chat.Chat(translate="test.format")

    assert chat.flatten() == "test.format"

    chat.load_translations({
        "test.format": "Test message",
    })

    assert chat.flatten() == "Test message"

    chat.load_translations({
        "test.format": "Test positional formatting %s %d",
    })

    chat.translate_with.extend([
        types.Chat.Chat("string", parent=chat),
        types.Chat.Chat("1",      parent=chat),
    ])

    assert chat.flatten() == "Test positional formatting string 1"

    chat.load_translations({
        "test.format": "Test indexed formatting %2$d %1$s"
    })

    assert chat.flatten() == "Test indexed formatting 1 string"

def test_load_translations(tmp_path):
    translation_path = tmp_path / "test_translations.json"

    with translation_path.open("w") as f:
        f.write('{"test.format":"Test message"}')

    chat = types.Chat.Chat(translate="test.format")
    chat.load_translations(translation_path)

    assert chat.flatten() == "Test message"

    with translation_path.open() as f:
        chat.load_translations(f)

    assert chat.flatten() == "Test message"

test_chat_type = assert_type_marshal_func(
    types.Chat,

    (types.Chat.Chat("test"), b'\x0F{"text":"test"}')
)
