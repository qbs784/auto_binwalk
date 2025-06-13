# Hardware File Auto-Download Tool

This Python project is designed to automatically download and extract hardware firmware files based on information from an Excel file.

## Features

- 📖 Read hardware list and download links from an Excel file
- 📥 Automatically download zip files to a specified directory
- 📦 Automatically extract downloaded files
- 🎯 **Keep only .bin files, automatically delete all other files and folders**
- 🗑️ Automatically delete zip archives after extraction
- 📊 Real-time download progress display
- 📝 Comprehensive logging
- 🔄 Error handling and retry mechanism

## Project Structure

```
auto-binwalk/
├── src/                        # Source code directory
│   └── download_hardware.py    # Main program
├── test/                       # Test files directory
│   ├── download_test.py        # Test script (processes only first 3 files)
│   └── test_setup.py           # Project configuration test
├── log/                        # Log files directory
│   ├── download.log            # Main program log
│   └── download_test.log       # Test script log
├── database/                   # Data directory
│   ├── hardware.xlsx           # Hardware info Excel file
│   ├── [hardware_name].bin     # Extracted .bin files (named by keyword)
│   └── [hardware_name]_2.bin   # If multiple .bin files, add numbering
├── run_download.py             # Main program runner script
├── run_test.py                 # Test runner script
├── run_setup_test.py           # Configuration test runner script
├── requirements.txt            # Dependency list
└── README.md                   # Project documentation
```

## Excel File Format

The `database/hardware.xlsx` file should contain at least two columns:

| Column Name   | Description      | Example                        |
|--------------|------------------|--------------------------------|
| keyword      | Hardware name    | Archer C50 V3                  |
| Download Link| Download URL     | https://static.tp-link.com/.../firmware.zip |

**Note:** The program will automatically detect the column structure and supports both 2-column and 3-column formats.

## Installation & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or, in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Prepare the Excel File

Make sure the `database/hardware.xlsx` file exists and contains the correct hardware information and download links.

### 3. Run the Program

**Configuration Test (recommended for first run):**
```bash
python3 run_setup_test.py
```

**Test Download (downloads only the first 3 files):**
```bash
python3 run_test.py
```

**Full Download (processes all files):**
```bash
python3 run_download.py
```

## Workflow

1. **Read Excel File:** Read hardware info from `database/hardware.xlsx`
2. **Validate Data:** Check the integrity of each row
3. **Download Files:** Download the corresponding zip file for each hardware
4. **Extract Files:** Automatically extract to a temporary folder
5. **Extract .bin Files:** Find and move all .bin files to the database directory
6. **Cleanup:** Delete the original zip archive and temporary folders, keep only .bin files
7. **Logging:** All operations are logged in the log directory

## Output

- Each hardware's .bin file is saved directly in the `database/` directory
- .bin files are named by keyword (e.g., `Archer_C50_V3.bin`)
- If a zip contains multiple .bin files, numbering is added to distinguish them
- Download progress and results are displayed in the terminal
- Detailed logs are saved in the `log/` directory
- **All non-.bin files are automatically deleted**

## Error Handling

The program includes robust error handling:

- **Network Errors:** Automatically skip files that cannot be downloaded
- **File Format Errors:** Handle non-zip or corrupted files
- **Data Validation:** Skip rows missing keyword or download link
- **File System Errors:** Handle permission and disk space issues

## Notes

- Ensure you have enough disk space for the downloaded files
- A stable network connection is recommended; large files may take longer to download
- The program adds a delay between requests to avoid overloading servers
- If the download is interrupted, you can safely rerun the program

## Log Files

Log files are saved in the `log/` directory:
- `download.log` - Main program log
- `download_test.log` - Test script log

Log contents include:
- Download start and finish times
- Download progress for each file
- Detailed extraction information
- Errors and warnings

## Dependencies

- **pandas:** For reading and processing Excel files
- **requests:** For HTTP downloads
- **openpyxl:** Backend engine for pandas to read Excel files

## License

This project is open-sourced under the MIT License.