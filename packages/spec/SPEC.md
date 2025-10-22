# AURA (Auditable Unified Representation for AI) Compression Format Specification

This document outlines the specification for the AURA (Auditable Unified Representation for AI) compression format.

## 1. Introduction

AURA is a streamable, AI-designed compression format with a focus on efficient client-side decompression and human-readable server-side representation. It is designed to facilitate efficient and auditable communication between AI systems and between users and AI systems.

The core innovation of AURA is its **hybrid structure**, combining a human-readable **Manifest** with a highly compressed, schema-dependent **Payload**.

## 2. File Structure

An AURA file or stream consists of three parts:

1.  **Header**: A fixed-size binary header.
2.  **Manifest**: A human-readable JSON object.
3.  **Payload**: A compact binary representation of the data.

```
+----------------+---------------------+-------------------+
|     Header     | Manifest (JSON)     |   Payload (Binary)|
+----------------+---------------------+-------------------+
```

### 2.1. Header

The header is 9 bytes long and contains:

*   **Magic Number** (4 bytes): The bytes `0x41555241` (the ASCII string "AURA").
*   **Version** (1 byte): The version of the AURA spec (e.g., `0x01`).
*   **Manifest Length** (4 bytes): A 32-bit unsigned integer representing the size of the Manifest in bytes.

### 2.2. Manifest

The Manifest is a UTF-8 encoded JSON object that describes the binary Payload. It must contain:

*   **`schema`**: A description of the data structure. This can be an object defining fields and their types (e.g., `{ "user": "string", "message": "string", "embeddings": "vec<f32>" }`).
*   **`dictionary`** (optional): An array of strings that are frequently used. The Payload can then refer to these strings by their index, saving space.
*   **`metadata`** (optional): An object for any auditable metadata, such as timestamps, data source, encryption status, etc.

### 2.3. Payload

The Payload is a binary encoding of the data that relies on the Manifest's `schema` and `dictionary` for interpretation. This separation is what allows for high efficiency.

#### Novel Concepts in Payload Encoding:

1.  **Shape-Based Serialization:** For objects whose structure is defined in the `schema`, the keys are **not** written to the payload. Only the values are written, in the order they appear in the schema. This provides a massive space saving over key-value formats like JSON.

2.  **Dictionary Encoding:** If a `dictionary` is provided in the Manifest, strings present in the dictionary are encoded as their integer index. A special escape mechanism is used for strings not found in the dictionary.

3.  **Specialized Types:** AURA defines high-performance types for common AI data structures.
    *   **`vec<f32>`**: A vector of 32-bit floating-point numbers. Encoded as a 4-byte integer for the count, followed by the raw bytes of the floats.
    *   **`vec<f16>`**: A vector of 16-bit floating-point numbers.

This design makes the Payload extremely compact and fast to parse, while the Manifest provides the necessary context for auditing and understanding the data.
