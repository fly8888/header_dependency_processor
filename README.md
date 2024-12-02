# Header Dependency Processor

## Overview
A Python tool for processing and optimizing Objective-C header file dependencies. It analyzes dependencies between header files, cleans header content, and generates optimized header files.

## Key Features
- Analyzes header file dependencies
- Cleans and optimizes header content
- Handles framework imports and protocol dependencies
- Generates dependency graphs
- Provides detailed processing logs

## Usage
1. Configure parameters:
   ```python
   headers_dir = "path/to/original/headers"
   target_header = "target_header_to_process"
   output_dir = "path/to/output/directory"
   ```

2. Run the program:
   ```bash
   python header_dependency_processor.py
   ```

## Features
- Automatic cleanup of .cxx_destruct methods
- Replacement of CDUnknownBlockType with id
- Protocol declaration optimization
- System framework import handling
- @class declaration processing
- Recursive dependency processing

## Logging
The program generates detailed processing logs including:
- Total number of processed files
- Total number of protocols found
- Dependency tree for each file

## Requirements
- Python 3.x
- OS: Cross-platform support

## Important Notes
- Ensure all required header files are present in the input directory
- Backup original files before processing 