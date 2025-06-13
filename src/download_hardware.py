#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware file download and extraction tool
Read hardware information from database/hardware.xlsx file, download corresponding zip files and automatically extract them
"""

import os
import pandas as pd
import requests
import zipfile
import logging
from pathlib import Path
from urllib.parse import urlparse, unquote
import time
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../log/download.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HardwareDownloader:
    def __init__(self, excel_file="../database/hardware.xlsx", download_dir="../database"):
        self.excel_file = excel_file
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
    def read_hardware_data(self):
        """Read hardware data from Excel file"""
        try:
            df = pd.read_excel(self.excel_file)
            logger.info(f"Successfully read Excel file: {self.excel_file}")
            logger.info(f"Found {len(df)} hardware records")
            return df
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            return None
    
    def get_filename_from_url(self, url):
        """Extract filename from URL"""
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if filename:
            return unquote(filename)
        else:
            return "download.zip"
    
    def download_file(self, url, keyword):
        """Download a single file"""
        try:
            logger.info(f"Starting download {keyword}: {url}")
            
            # Send request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine filename
            filename = self.get_filename_from_url(url)
            if not filename.endswith('.zip'):
                filename = f"{keyword}.zip"
            
            file_path = self.download_dir / filename
            
            # Download file
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            logger.info(f"Download progress {keyword}: {percent:.1f}%")
            
            logger.info(f"Download completed: {filename}")
            return file_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed {keyword}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error occurred during download {keyword}: {e}")
            return None
    
    def extract_zip(self, zip_path, keyword):
        """Extract zip file and keep only .bin files"""
        try:
            # Create temporary extraction directory
            safe_keyword = keyword.replace(' ', '_').replace('/', '_').replace('\\', '_')
            temp_extract_dir = self.download_dir / f"temp_{safe_keyword}"
            temp_extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get list of files in the archive
                file_list = zip_ref.namelist()
                logger.info(f"Extracting {keyword}: Found {len(file_list)} files")
                
                # Extract all files to temporary directory
                zip_ref.extractall(temp_extract_dir)
            
            # Find .bin files
            bin_files = []
            for root, dirs, files in os.walk(temp_extract_dir):
                for file in files:
                    if file.lower().endswith('.bin'):
                        bin_files.append(os.path.join(root, file))
            
            if not bin_files:
                logger.warning(f"No .bin files found: {keyword}")
                # Clean up temporary directory
                shutil.rmtree(temp_extract_dir)
                zip_path.unlink()
                return False
            
            # Move .bin files to database directory
            moved_files = []
            for bin_file_path in bin_files:
                bin_filename = os.path.basename(bin_file_path)
                
                # If multiple .bin files exist, add keyword prefix to avoid conflicts
                if len(bin_files) > 1:
                    new_filename = f"{safe_keyword}_{bin_filename}"
                else:
                    # If only one .bin file exists, rename it with keyword
                    file_extension = os.path.splitext(bin_filename)[1]
                    new_filename = f"{safe_keyword}{file_extension}"
                
                # Ensure unique filename
                counter = 1
                final_filename = new_filename
                while (self.download_dir / final_filename).exists():
                    name_part, ext_part = os.path.splitext(new_filename)
                    final_filename = f"{name_part}_{counter}{ext_part}"
                    counter += 1
                
                dest_path = self.download_dir / final_filename
                shutil.move(bin_file_path, dest_path)
                moved_files.append(final_filename)
                logger.info(f"Moved .bin file: {bin_filename} -> {final_filename}")
            
            # Clean up temporary directory
            shutil.rmtree(temp_extract_dir)
            logger.info(f"Cleaned up temporary files, kept .bin files: {', '.join(moved_files)}")
            
            # Delete original zip file
            zip_path.unlink()
            logger.info(f"Deleted zip file: {zip_path.name}")
            
            return True
            
        except zipfile.BadZipFile:
            logger.error(f"Invalid zip file: {zip_path}")
            return False
        except Exception as e:
            logger.error(f"Extraction failed {keyword}: {e}")
            # Clean up temporary directory if it exists
            if 'temp_extract_dir' in locals() and temp_extract_dir.exists():
                try:
                    shutil.rmtree(temp_extract_dir)
                except:
                    pass
            return False
    
    def process_all_hardware(self):
        """Process all hardware downloads"""
        # Read Excel data
        df = self.read_hardware_data()
        if df is None:
            return
        
        # Check column names
        columns = df.columns.tolist()
        logger.info(f"Excel file columns: {columns}")
        
        # Use correct columns based on actual Excel file structure
        if len(columns) < 2:
            logger.error("Excel file needs at least two columns")
            return
        
        keyword_col = columns[0]  # First column is keyword
        # If there are 3 columns, use the last column; if only 2 columns, use the second column
        if len(columns) >= 3:
            link_col = columns[2]  # Third column is Download Link
        else:
            link_col = columns[1]  # Second column is Download Link
        
        logger.info(f"Using columns: keyword='{keyword_col}', download_link='{link_col}'")
        
        success_count = 0
        total_count = len(df)
        
        for index, row in df.iterrows():
            keyword = str(row[keyword_col]).strip()
            download_link = str(row[link_col]).strip()
            
            if pd.isna(keyword) or pd.isna(download_link) or keyword == 'nan' or download_link == 'nan':
                logger.warning(f"Skipping row {index+1}: Missing keyword or download link")
                continue
            
            logger.info(f"Processing ({index+1}/{total_count}): {keyword}")
            
            # Download file
            zip_path = self.download_file(download_link, keyword)
            if zip_path is None:
                continue
            
            # Extract file
            if self.extract_zip(zip_path, keyword):
                success_count += 1
            
            # Add delay to avoid too frequent requests
            time.sleep(1)
        
        logger.info(f"Processing completed: Success {success_count}/{total_count}")

def main():
    """Main function"""
    logger.info("Starting hardware file download task")
    
    # Check if Excel file exists
    excel_file = "../database/hardware.xlsx"
    if not os.path.exists(excel_file):
        logger.error(f"Excel file does not exist: {excel_file}")
        return
    
    # Create downloader and start processing
    downloader = HardwareDownloader()
    downloader.process_all_hardware()
    
    logger.info("Hardware file download task completed")

if __name__ == "__main__":
    main() 