"""End-to-end scenarios covering human→AI and AI→AI style messages."""

from pathlib import Path
import sys

PACKAGE_SRC = Path(__file__).resolve().parent.parent / "packages" / "aura-compressor-py" / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from aura_compressor.streamer import AuraStreamSession


def test_human_to_ai_message_hits_template():
    session = AuraStreamSession()
    message = "Can you help me debug this issue?"

    encoded = session.encode_message(message)
    decoded = session.decode_message(encoded)

    assert encoded.method == "template"
    assert encoded.metadata.get("compression") == "template"
    assert decoded == message


def test_ai_to_ai_message_hits_template():
    session = AuraStreamSession()
    message = "I don't have access to your calendar."

    encoded = session.encode_message(message)
    decoded = session.decode_message(encoded)

    assert encoded.method == "template"
    assert encoded.metadata.get("compression") == "template"
    assert decoded == message
