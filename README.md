# Auto Binwalk

An automated tool for downloading firmware, performing binwalk analysis, and conducting AI-powered security reviews.

## Features

### 1. Firmware Download
- Support for multiple firmware download sources
- Automatic firmware version detection
- Parallel download capability
- Download progress tracking
- Automatic retry mechanism
- Support for different download protocols (HTTP/HTTPS/FTP)

### 2. Binwalk Analysis
- Automatic firmware extraction and analysis
- Support for multiple file formats
- Detailed analysis report generation
- Extraction of embedded files and file systems
- Identification of file signatures and magic numbers
- Support for entropy analysis

### 3. AI Security Review
- Automated security analysis of firmware
- Identification of potential security vulnerabilities
- Analysis of file system structure
- Detection of sensitive information
- Generation of comprehensive security reports
- Integration with OpenAI's GPT models for intelligent analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/auto-binwalk.git
cd auto-binwalk

# Install dependencies
pip install -e .
```

## Usage

### 1. Download Firmware
```bash
# Download firmware from a specific URL
python run_download.py --url "https://example.com/firmware.bin"

# Download firmware with specific version
python run_download.py --url "https://example.com/firmware.bin" --version "1.0.0"

# Download firmware with custom output directory
python run_download.py --url "https://example.com/firmware.bin" --output-dir "./firmware"
```

### 2. Run Binwalk Analysis
```bash
# Analyze a firmware file
python run_binwalk_api.py --firmware "path/to/firmware.bin"

# Analyze with specific options
python run_binwalk_api.py --firmware "path/to/firmware.bin" --extract --entropy

# Analyze and save results
python run_binwalk_api.py --firmware "path/to/firmware.bin" --output "analysis_results.json"
```

### 3. Perform AI Security Review
```bash
# Review firmware analysis results
python run_binwalk_api.py --firmware "path/to/firmware.bin" --review

# Review with specific AI model
python run_binwalk_api.py --firmware "path/to/firmware.bin" --review --model "gpt-4"

# Review and save report
python run_binwalk_api.py --firmware "path/to/firmware.bin" --review --output "security_report.json"
```

## Configuration

The tool can be configured through environment variables or a configuration file:

```bash
# Environment variables
export OPENAI_API_KEY="your-api-key"
export DOWNLOAD_TIMEOUT=300
export MAX_RETRIES=3
```

## Project Structure

```
auto-binwalk/
├── src/
│   ├── download_hardware.py      # Firmware download module
│   ├── binwalk_api_analyzer.py   # Binwalk analysis module
│   └── binwalk_review_analyzer.py # AI review module
├── test/
│   └── test_setup.py            # Test cases
├── run_download.py              # Download script
├── run_binwalk_api.py          # Analysis script
└── setup.py                    # Installation script
```

## Dependencies

- Python 3.8+
- binwalk
- requests
- openai
- tqdm
- colorama
- python-dotenv

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request