#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firmware analyzer using binwalk Python API
Version compatibility handling to avoid dep module issues
"""

import os
import sys
import logging
from pathlib import Path
import json
from datetime import datetime

# Configure logging
log_dir = Path('log')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/binwalk_api_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BinwalkAPIAnalyzer:
    def __init__(self, bin_dir="database", output_dir="api_analysis_results"):
        self.bin_dir = Path(bin_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.extracted_dir = self.output_dir / "extracted"
        self.reports_dir = self.output_dir / "reports"
        self.extracted_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        self._check_binwalk_api()
    
    def _check_binwalk_api(self):
        """Check if binwalk API is available"""
        try:
            # First try to fix imp module issues
            self._patch_imp_module()
            
            import binwalk
            self.binwalk = binwalk
            return True
        except Exception as e:
            logger.error(f"binwalk API not available: {e}")
            logger.info("Will use command line method as fallback")
            self.binwalk = None
            return False
    
    def _patch_imp_module(self):
        """Fix imp module compatibility issues"""
        try:
            import imp
        except ModuleNotFoundError:
            # imp module removed in Python 3.12+, provide alternative implementation
            import importlib.util
            import types
            
            class ImpReplacement:
                PY_SOURCE = 1
                PY_COMPILED = 2
                C_EXTENSION = 3
                
                @staticmethod
                def find_module(name, path=None):
                    try:
                        spec = importlib.util.find_spec(name, path)
                        if spec is None:
                            return None
                        return (None, spec.origin, ('', '', ImpReplacement.PY_SOURCE))
                    except:
                        return None
                
                @staticmethod
                def load_module(name, file, pathname, description):
                    try:
                        spec = importlib.util.spec_from_file_location(name, pathname)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        return module
                    except:
                        return None
                
                @staticmethod
                def load_source(name, pathname, file=None):
                    try:
                        spec = importlib.util.spec_from_file_location(name, pathname)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        return module
                    except:
                        return None
            
            # Inject alternative implementation into sys.modules
            sys.modules['imp'] = ImpReplacement()
            logger.info("Fixed imp module compatibility issues")
    
    def get_bin_files(self):
        """Get all .bin files"""
        bin_files = []
        try:
            for file_path in self.bin_dir.glob("*.bin"):
                if file_path.is_file():
                    bin_files.append(file_path)
            logger.info(f"Found {len(bin_files)} .bin files")
            return bin_files
        except Exception as e:
            logger.error(f"Error occurred while getting .bin file list: {e}")
            return []
    
    def analyze_with_api(self, bin_file):
        """Analyze file using binwalk API"""
        if self.binwalk is None:
            raise RuntimeError("binwalk API not available")
        
        filename = bin_file.stem
        results = {
            'filename': str(bin_file),
            'api_results': {}
        }
        
        try:
            logger.info(f"Scanning with API: {filename}")
            
            # 1. Basic signature scan
            scan_results = []
            for module in self.binwalk.scan(str(bin_file)):
                for result in module.results:
                    scan_results.append({
                        'offset': result.offset,
                        'description': result.description,
                        'file_path': result.file_path
                    })
            
            results['api_results']['signature_scan'] = {
                'results': scan_results,
                'count': len(scan_results)
            }
            
            # 2. Extract files
            logger.info(f"Extracting files with API: {filename}")
            extract_dir = self.extracted_dir / filename
            extract_dir.mkdir(exist_ok=True)
            
            extraction_results = []
            for module in self.binwalk.scan(str(bin_file), 
                                         signature=True, 
                                         quiet=True, 
                                         extract=True,
                                         directory=str(extract_dir)):
                for result in module.results:
                    extraction_results.append({
                        'offset': result.offset,
                        'description': result.description,
                        'extracted': getattr(result, 'extracted', False)
                    })
            
            results['api_results']['extraction'] = {
                'results': extraction_results,
                'count': len(extraction_results),
                'extract_directory': str(extract_dir)
            }
            
            logger.info(f"API analysis completed: {filename}")
            return results
            
        except Exception as e:
            logger.error(f"API analysis failed {filename}: {e}")
            results['error'] = str(e)
            return results
    
    def analyze_with_command(self, bin_file):
        """Analyze using command line method (fallback)"""
        import subprocess
        
        filename = bin_file.stem
        results = {
            'filename': str(bin_file),
            'command_results': {}
        }
        
        try:
            # Basic scan
            logger.info(f"Scanning with command line: {filename}")
            cmd = ['binwalk', str(bin_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            results['command_results']['signature_scan'] = {
                'command': ' '.join(cmd),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
            # Extract
            extract_dir = self.extracted_dir / filename
            extract_dir.mkdir(exist_ok=True)
            
            logger.info(f"Extracting with command line: {filename}")
            cmd = ['binwalk', '--extract', '--matryoshka', str(bin_file), '--directory', str(extract_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            results['command_results']['extraction'] = {
                'command': ' '.join(cmd),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'extract_directory': str(extract_dir)
            }
            
            logger.info(f"Command line analysis completed: {filename}")
            return results
            
        except Exception as e:
            logger.error(f"Command line analysis failed {filename}: {e}")
            results['error'] = str(e)
            return results
    
    def analyze_firmware(self, bin_file):
        """Analyze firmware file"""
        filename = bin_file.stem
        logger.info(f"Starting firmware analysis: {bin_file.name}")
        
        # Try API first, fall back to command line if it fails
        if self.binwalk is not None:
            try:
                return self.analyze_with_api(bin_file)
            except Exception as e:
                logger.warning(f"API analysis failed, switching to command line mode: {e}")
                return self.analyze_with_command(bin_file)
        else:
            return self.analyze_with_command(bin_file)
    
    def save_analysis_report(self, filename, results):
        """Save analysis report"""
        try:
            # Generate report data
            report_data = {
                'firmware_name': filename,
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'API' if 'api_results' in results else 'Command',
                'results': results
            }
            
            # Save JSON format report
            json_report_path = self.reports_dir / f"{filename}_api_analysis.json"
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            # Save text report
            txt_report_path = self.reports_dir / f"{filename}_api_analysis.txt"
            with open(txt_report_path, 'w', encoding='utf-8') as f:
                f.write(f"Firmware analysis report (API mode): {filename}\n")
                f.write(f"Analysis time: {report_data['analysis_timestamp']}\n")
                f.write(f"Analysis method: {report_data['analysis_method']}\n")
                f.write("=" * 80 + "\n\n")
                
                if 'api_results' in results:
                    self._write_api_results(f, results['api_results'])
                elif 'command_results' in results:
                    self._write_command_results(f, results['command_results'])
                
                if 'error' in results:
                    f.write(f"Error: {results['error']}\n")
            
            logger.info(f"Analysis report saved: {json_report_path.name} and {txt_report_path.name}")
            
        except Exception as e:
            logger.error(f"Error occurred while saving analysis report: {e}")
    
    def _write_api_results(self, f, api_results):
        """Write API results"""
        for analysis_type, data in api_results.items():
            f.write(f"{analysis_type.upper()}\n")
            f.write("-" * 40 + "\n")
            
            if 'results' in data:
                f.write(f"Found {data['count']} results:\n")
                for i, result in enumerate(data['results'][:10]):  # Only show first 10
                    f.write(f"  {i+1}. Offset: {result.get('offset', 'N/A')}, Description: {result.get('description', 'N/A')}\n")
                if data['count'] > 10:
                    f.write(f"  ... {data['count'] - 10} more results\n")
            
            if 'extract_directory' in data:
                f.write(f"Extracted directory: {data['extract_directory']}\n")
            
            f.write("\n")
    
    def _write_command_results(self, f, cmd_results):
        """Write command line results"""
        for analysis_type, data in cmd_results.items():
            f.write(f"{analysis_type.upper()}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Command: {data['command']}\n")
            f.write(f"Return code: {data['returncode']}\n")
            if data['stdout']:
                f.write(f"Output:\n{data['stdout']}\n")
            if data['stderr']:
                f.write(f"Error:\n{data['stderr']}\n")
            f.write("\n")
    
    def analyze_all_firmware(self):
        """Analyze all firmware files"""
        logger.info("Starting batch firmware analysis (API mode)")
        
        # Get all .bin files
        bin_files = self.get_bin_files()
        if not bin_files:
            logger.warning("No .bin files found")
            return
        
        success_count = 0
        total_count = len(bin_files)
        
        for i, bin_file in enumerate(bin_files, 1):
            logger.info(f"Processing progress: {i}/{total_count}")
            try:
                results = self.analyze_firmware(bin_file)
                self.save_analysis_report(bin_file.stem, results)
                success_count += 1
            except Exception as e:
                logger.error(f"Error occurred while analyzing {bin_file.name}: {e}")
        
        logger.info(f"Batch analysis completed: Success {success_count}/{total_count}")
        logger.info(f"Analysis results saved in: {self.output_dir}")

def main():
    """Main function"""
    logger.info("Starting binwalk API firmware analysis")
    
    # Create analyzer
    analyzer = BinwalkAPIAnalyzer()
    
    # Analyze all firmware
    analyzer.analyze_all_firmware()
    
    logger.info("binwalk API firmware analysis completed")

if __name__ == "__main__":
    main() 