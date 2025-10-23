from aura_compression.compressor import CompressionMethod, ProductionHybridCompressor
from aura_compression.experimental.auralite import AuraLiteDecoder, AuraLiteEncoder
from aura_compression.templates import TemplateLibrary


def test_auralite_encoder_decoder_roundtrip():
    encoder = AuraLiteEncoder()
    template_library = TemplateLibrary()
    decoder = AuraLiteDecoder(template_library=template_library)

    text = "Yes, I can help with that. Please check system status."
    encoded = encoder.encode(text)

    decoded = decoder.decode(encoded.payload)
    assert decoded.text == text
    assert decoded.template_ids == encoded.template_ids


def test_hybrid_compressor_uses_auralite_for_template_heavy_text():
    compressor = ProductionHybridCompressor(
        binary_advantage_threshold=5.0,
        min_compression_size=0,
        enable_aura=False,
        aura_preference_margin=0.0,
    )

    text = (
        "Yes, I can help with that. "
        "Please check system performance data and monitor deployment status."
    )

    compressed, method, metadata = compressor.compress(text)
    assert method == CompressionMethod.AURA_LITE
    assert metadata['method'] == 'aura_lite'

    decompressed = compressor.decompress(compressed)
    assert decompressed == text


def test_auralite_encodes_inline_template_spans():
    template_library = TemplateLibrary()
    encoder = AuraLiteEncoder()
    decoder = AuraLiteDecoder(template_library=template_library)

    snippet = template_library.format_template(
        130,
        [
            "dashboard",
            "Let me outline the diagnostics flow so you have a concrete sequence to follow.",
        ],
    )
    text = f"Please review the plan first. {snippet} Additional note."

    spans = template_library.find_substring_matches(text)
    assert spans, "Expected substring template matches"

    encoded = encoder.encode(text, template_spans=spans)
    decoded = decoder.decode(encoded.payload)

    assert decoded.text == text
    assert decoded.template_ids == [match.template_id for match in spans]
