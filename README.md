# pybrp

This is `pybrp`, a Python library for working with `.brp` files. These are BombSquad's replay files, which basically contain a stream of game messages.

It helps you out by:

* **Huffman Decompression**: Handles the custom compression found in `.brp` files.
* **Full File Decompression**: Can decompress an entire `.brp` file, writing the uncompressed messages to a new file.
* **Duration Calculation**: Figures out the total time (in milliseconds) of events in a `.brp` file. Note that `.brp` files don't store explicit timestamps; the duration is deduced from the messages.
* **Structured Data Extraction**: Parses the messages and their arguments into a readable dictionary format.
* **Progress Tracking**: Provides a way to track progress during file operations by passing a callback function.

## Installation

Just copy the `pybrp.py` file into your project directory. No complex setup needed.

## Usage

First, import what you need and set up the decompressor:

```python
from pybrp import _H, get_duration, decompress, get_data

# Initialize the Huffman decompressor
huffman_decompressor = _H()

# A simple function for showing progress updates
def console_progress(current, total):
    print(f"Processing: {current/total:.1%} ({current}/{total} bytes)", end='\r')
```

### Getting Total Event Duration

Find out the total duration of events in a `.brp` file. You can also pass an optional `progress` callback.

```python
brp_file_path = "path/to/your/replay.brp"

try:
    # Example: Get duration
    total_ms = get_duration(huffman_decompressor, brp_file_path)
    print(f"Total duration: {total_ms} ms")

    # Example: Get duration with a progress callback
    total_ms_with_progress = get_duration(huffman_decompressor, brp_file_path, progress=console_progress)
    print(f"\nTotal duration (with progress): {total_ms_with_progress} ms")
except Exception as e:
    print(f"Error getting duration: {e}")
```

### Decompressing a .brp File

Decompress a `.brp` file's internal messages to a new output file.

```python
input_path = "path/to/your/compressed_file.brp"
output_path = "path/to/your/decompressed_file.brp"

try:
    # Example: Decompress a file
    decompress(huffman_decompressor, input_path, output_path)
    print(f"\nFile decompressed to: {output_path}")
except Exception as e:
    print(f"Error decompressing file: {e}")
```

### Extracting and Parsing Event Data

Get structured event data from a `.brp` file. By default, arguments are parsed into Python types.

**Parameters**:
* `as_hex=True`: Get raw hexadecimal payloads for command arguments instead of parsed values. Useful for debugging or unhandled command types.
* `progress`: (Optional) A callback function for progress updates (e.g., `console_progress`).

```python
brp_file_path = "path/to/your/replay_data.brp"

try:
    # Example 1: Get parsed data
    event_data_parsed = get_data(huffman_decompressor, brp_file_path)
    print("\nExtracted Event Data Sample (Parsed):")
    for timestamp, commands in list(event_data_parsed.items())[:5]: # Showing first 5 timestamps
        print(f"  Timestamp: {timestamp} ms")
        for command in commands[:2]: # Showing first 2 commands per timestamp
            print(f"    - Command: {command['name']}, Args: {command.get('args', 'N/A')}")

    # Example 2: Get raw hexadecimal data
    raw_event_data_hex = get_data(huffman_decompressor, brp_file_path, as_hex=True)
    print("\nRaw Event Data Sample (Hex):")
    for timestamp, commands in list(raw_event_data_hex.items())[:1]: # Showing first timestamp
        for command in commands[:1]: # Showing first command
            print(f"    - Command: {command['name']}, Data Hex: {command.get('data_hex', 'N/A')}")

except Exception as e:
    print(f"Error extracting data: {e}")
```

## Internal Structure

This library was developed by referencing BombSquad's publicly available C++ source code.

* `_H`: The main Huffman decompressor class.
* `G_FREQS`: The global frequency table for Huffman tree construction, adapted directly from BombSquad's C++ source.
* `CMD_NAMES`: A dictionary mapping command IDs to their string names.
* `COMMAND_PARSERS`: Maps command IDs to functions responsible for parsing their specific arguments.
* `_DataReader`: An internal utility for reading various data types from binary streams.

## Error Handling

Functions will raise standard Python exceptions (`FileNotFoundError`, `ValueError`) for file or decompression issues. If `get_data` encounters a parsing error when `as_hex` is `False`, it will include the raw hexadecimal data for that command and an `error` key in the output, allowing for debugging.
