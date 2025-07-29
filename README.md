# pybrp

`pybrp` is a Python library designed for parsing and interacting with `.brp` binary files. These files typically contain time-sequenced scene graph data or game commands.

## Features

* **Huffman Decompression**: Efficiently decompresses `.brp` file contents using a custom Huffman algorithm.
* **File Decompression Utility**: Provides a function to decompress entire `.brp` files, writing the uncompressed message streams to a new file.
* **Event Duration Calculation**: Quickly determines the total duration (in milliseconds) of events within a `.brp` file without full content parsing.
* **Structured Data Extraction**: Parses commands and their arguments from `.brp` files into a structured dictionary, supporting various native data types.
* **Progress Monitoring**: All major file operations support an optional callback for progress updates.

## Installation

Simply include the `pybrp.py` file directly in your project.

## Usage

Start by importing the necessary components and initializing the decompressor:

```python
from pybrp import _H, get_duration, decompress, get_data

# Initialize the Huffman decompressor
huffman_decompressor = _H()

# Optional: A simple progress callback for file operations
def console_progress(current, total):
    print(f"Processing: {current/total:.1%} ({current}/{total} bytes)", end='\r')
```

### Get Total Event Duration

Calculate the total duration of events in a `.brp` file:

```python
brp_file_path = "path/to/your/file.brp"

try:
    total_ms = get_duration(huffman_decompressor, brp_file_path, progress=console_progress)
    print(f"\nTotal event duration: {total_ms} ms")
except Exception as e:
    print(f"Error getting duration: {e}")
```

### Decompress a .brp File

Decompress the internal messages of a `.brp` file to a new, structurally similar file:

```python
input_path = "path/to/your/compressed.brp"
output_path = "path/to/your/decompressed.brp"

try:
    decompress(huffman_decompressor, input_path, output_path, progress=console_progress)
    print(f"\nFile decompressed to: {output_path}")
except Exception as e:
    print(f"Error decompressing file: {e}")
```

### Extract and Parse Event Data

Retrieve structured event data from a `.brp` file. By default, arguments are parsed into Python types.

```python
brp_file_path = "path/to/your/file.brp"

try:
    event_data = get_data(huffman_decompressor, brp_file_path, progress=console_progress)
    print("\nExtracted Event Data Sample:")
    for timestamp, commands in list(event_data.items())[:5]: # Showing first 5 timestamps
        print(f"  Timestamp: {timestamp} ms")
        for command in commands[:2]: # Showing first 2 commands per timestamp
            print(f"    - Command: {command['name']}, Args: {command.get('args', 'N/A')}")

    # To retrieve raw hexadecimal payloads (useful for unknown commands or debugging parsing issues):
    # raw_event_data = get_data(huffman_decompressor, brp_file_path, as_hex=True, progress=console_progress)
    # print("\nRaw Event Data Sample (Hex):")
    # for timestamp, commands in list(raw_event_data.items())[:1]: # Showing first timestamp
    #     for command in commands[:1]: # Showing first command
    #         print(f"    - Command: {command['name']}, Data Hex: {command.get('data_hex', 'N/A')}")

except Exception as e:
    print(f"Error extracting data: {e}")
```

## Internal Structure

* `_H`: Huffman decompressor class, pre-configured with `G_FREQS`.
* `G_FREQS`: Global frequency table for Huffman tree construction.
* `CMD_NAMES`: Dictionary mapping command IDs to their string names.
* `COMMAND_PARSERS`: Maps command IDs to specific parsing functions for argument deserialization.
* `_DataReader`: Internal helper for reading binary data streams.

## Error Handling

Functions raise standard Python exceptions (`FileNotFoundError`, `ValueError`) for file-related or decompression issues. `get_data` includes internal handling for parsing errors, providing raw hexadecimal data and an error message for problematic command payloads when `as_hex` is `False`.
