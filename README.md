# pybrp

The **pybrp** library provides a set of Python utilities for interacting with `.brp` files. These files appear to be a proprietary binary format, likely used for representing scene graph data, game commands, or other time-sequenced event streams. The library encompasses functionalities for decompression, parsing, and data extraction, including total duration and detailed event payloads.

## Features

* **Huffman Decompression**: Implements a custom Huffman decompression algorithm specifically tailored for the `.brp` file structure.
* **File Decompression**: Supports decompressing the internal message payloads of an entire `.brp` file, writing the uncompressed data to a new output file. The file's structural elements (e.g., headers, message length indicators) are preserved.
* **Duration Calculation**: Efficiently determines the total duration (in milliseconds) of recorded events within a `.brp` file, avoiding full command parsing for this operation.
* **Data Extraction and Parsing**: Extracts and parses individual commands and their arguments from `.brp` files. The output is a structured dictionary, with support for various command types and their native data formats (float, integer, boolean, string, array types).
* **Progress Tracking**: All file processing functions offer an optional progress callback, suitable for integration into user interfaces or logging systems.

## Installation

This library is distributed as a single Python module. To integrate it into your project, simply copy `pybrp.py` into your project directory or make it accessible on your Python path.

## Usage

To utilize the library, begin by importing the necessary components and instantiating the Huffman decompressor:

```python
from pybrp import _H, get_duration, decompress, get_data

# Initialize the Huffman decompressor instance
huffman_decompressor = _H()

# Define a common progress callback function for examples
def print_progress(current, total):
    print(f"Progress: {current}/{total} bytes ({current/total:.2%})", end='\r')
```

### Calculating File Duration

To retrieve the total elapsed time of events within a `.brp` file:

**Signature:** `get_duration(_h, brp_path, progress=None)`

```python
brp_file_path = "path/to/your/file.brp"

# Example 1: Calculate duration without progress tracking
try:
    total_ms = get_duration(huffman_decompressor, brp_file_path)
    print(f"Total duration (no progress): {total_ms} ms")
except FileNotFoundError:
    print(f"Error: Source file not found at {brp_file_path}")
except ValueError as e:
    print(f"Error processing file: {e}")

# Example 2: Calculate duration with progress tracking
try:
    total_ms_with_progress = get_duration(huffman_decompressor, brp_file_path, progress=print_progress)
    print(f"\nTotal duration (with progress): {total_ms_with_progress} ms")
except FileNotFoundError:
    print(f"Error: Source file not found at {brp_file_path}")
except ValueError as e:
    print(f"Error processing file: {e}")
```

### Decompressing a .brp File

To decompress the message payloads within a `.brp` file, writing the result to a new file:

**Signature:** `decompress(_h, brp_path, output_path, progress=None)`

```python
input_brp_path = "path/to/your/compressed.brp"
output_brp_path = "path/to/your/decompressed.brp"

# Example 1: Decompress without progress tracking
try:
    decompress(huffman_decompressor, input_brp_path, output_brp_path)
    print(f"\nDecompression complete (no progress): '{input_brp_path}' -> '{output_brp_path}'")
except FileNotFoundError:
    print(f"Error: Input file not found at {input_brp_path}")
except Exception as e:
    print(f"Error during decompression: {e}")

# Example 2: Decompress with progress tracking
output_brp_path_with_progress = "path/to/your/decompressed_with_progress.brp"
try:
    decompress(huffman_decompressor, input_brp_path, output_brp_path_with_progress, progress=print_progress)
    print(f"\nDecompression complete (with progress): '{input_brp_path}' -> '{output_brp_path_with_progress}'")
except FileNotFoundError:
    print(f"Error: Input file not found at {input_brp_path}")
except Exception as e:
    print(f"Error during decompression: {e}")
```

### Extracting and Parsing Data

To obtain a structured representation of all commands and their arguments, grouped by timestamp:

**Signature:** `get_data(_h, brp_path, as_hex=False, progress=None)`

```python
brp_file_path = "path/to/your/file.brp"

# Example 1: Extract and parse data (default: as_hex=False, no progress)
try:
    event_data_parsed = get_data(huffman_decompressor, brp_file_path)
    print("\nExtracted Event Data (Parsed, No Progress):")
    # Display a snippet to avoid overwhelming output
    for timestamp, commands in list(event_data_parsed.items())[:3]: # Show first 3 timestamps
        print(f"Timestamp: {timestamp} ms")
        for command in commands[:1]: # Show first command per timestamp
            print(f"  - Command: {command['name']}, Args: {command.get('args', 'N/A')}")
except FileNotFoundError:
    print(f"Error: File not found at {brp_file_path}")
except ValueError as e:
    print(f"Error processing file: {e}")

# Example 2: Extract data as raw hex (as_hex=True, no progress)
try:
    event_data_hex = get_data(huffman_decompressor, brp_file_path, as_hex=True)
    print("\nExtracted Event Data (Raw Hex, No Progress):")
    for timestamp, commands in list(event_data_hex.items())[:3]: # Show first 3 timestamps
        print(f"Timestamp: {timestamp} ms")
        for command in commands[:1]: # Show first command per timestamp
            print(f"  - Command: {command['name']}, Raw Data (Hex): {command.get('data_hex', 'N/A')}")
except FileNotFoundError:
    print(f"Error: File not found at {brp_file_path}")
except ValueError as e:
    print(f"Error processing file: {e}")

# Example 3: Extract and parse data with progress (as_hex=False, progress=print_progress)
try:
    event_data_parsed_progress = get_data(huffman_decompressor, brp_file_path, as_hex=False, progress=print_progress)
    print("\nExtracted Event Data (Parsed, With Progress):")
    for timestamp, commands in list(event_data_parsed_progress.items())[:3]: # Show first 3 timestamps
        print(f"Timestamp: {timestamp} ms")
        for command in commands[:1]: # Show first command per timestamp
            print(f"  - Command: {command['name']}, Args: {command.get('args', 'N/A')}")
except FileNotFoundError:
    print(f"Error: File not found at {brp_file_path}")
except ValueError as e:
    print(f"Error processing file: {e}")

# Example 4: Extract data as raw hex with progress (as_hex=True, progress=print_progress)
try:
    event_data_hex_progress = get_data(huffman_decompressor, brp_file_path, as_hex=True, progress=print_progress)
    print("\nExtracted Event Data (Raw Hex, With Progress):")
    for timestamp, commands in list(event_data_hex_progress.items())[:3]: # Show first 3 timestamps
        print(f"Timestamp: {timestamp} ms")
        for command in commands[:1]: # Show first command per timestamp
            print(f"  - Command: {command['name']}, Raw Data (Hex): {command.get('data_hex', 'N/A')}")
except FileNotFoundError:
    print(f"Error: File not found at {brp_file_path}")
except ValueError as e:
    print(f"Error processing file: {e}")
```

## Data Structures and Internals

* `_H` (Huffman Decompressor Class): Manages the Huffman tree construction and decompression logic.
    * `_N` (Node Class): An internal helper class representing nodes within the Huffman tree structure.
    * `__init__`: Initializes the Huffman tree based on `G_FREQS`.
    * `decompress(src)`: Performs Huffman decompression on the provided byte string.
* `G_FREQS`: A hardcoded list defining the global frequencies used for Huffman tree construction, essential for correct decompression.
* `CMD_NAMES`: A dictionary mapping numerical command identifiers to their corresponding string names. Access via `pybrp.CMD_NAMES`.
* `_DataReader`: An internal utility class for sequential reading of various data types from a byte stream during command parsing.
* `COMMAND_PARSERS`: An internal dictionary mapping command IDs to specific parsing functions, facilitating dynamic and structured argument extraction for different command types.

## Error Handling

The library's functions implement basic error handling for common issues such as `FileNotFoundError` and `ValueError` (e.g., incomplete Huffman codes during decompression). Within the `get_data` function, if `as_hex` is `False` and a command's argument parsing encounters an exception, the `'args'` field for that command will contain an error message, and the `'data_hex'` field will provide the raw hexadecimal payload for debugging.
