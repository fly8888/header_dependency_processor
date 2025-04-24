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
1. Run the program with required arguments:
   ```bash
   python header_dependency_processor.py <source_headers_dir> <output_dir> <wx_header_path>
   ```

   Where:
   - `source_headers_dir`: Directory containing the original header files
   - `output_dir`: Directory where processed files will be saved
   - `wx_header_path`: Path to your Header.h file

The script will:
- Process all headers imported in Header.h
- Clean and optimize the header contents
- Save processed files to the output directory
- Generate detailed logs of the process

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