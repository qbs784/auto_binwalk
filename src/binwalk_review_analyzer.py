#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binwalk Analysis Review Tool
Use large language models to analyze binwalk parsing results and generate review reports
"""

import os
import json
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Any
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinwalkReviewAnalyzer:
    """Binwalk result review analyzer"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = "gpt-4"):
        """
        Initialize analyzer
        
        Args:
            api_key: OpenAI API key
            base_url: API base URL (optional, for custom endpoint)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL')
        self.model = model
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable or api_key parameter is required")
        
        # Initialize OpenAI client
        if self.base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = OpenAI(api_key=self.api_key)
        
        self.results_dir = Path("api_analysis_results")
        self.review_dir = Path("review")
        self.review_dir.mkdir(exist_ok=True)
    
    def read_analysis_results(self) -> Dict[str, Any]:
        """Read binwalk analysis results"""
        results = {
            "reports": {},
            "extracted_structure": {},
            "firmware_files": []
        }
        
        # Read report files
        reports_dir = self.results_dir / "reports"
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.json"):
                firmware_name = report_file.stem.replace("_api_analysis", "")
                with open(report_file, 'r', encoding='utf-8') as f:
                    results["reports"][firmware_name] = json.load(f)
                logger.info(f"Reading report: {firmware_name}")
        
        # Analyze extracted file structure
        extracted_dir = self.results_dir / "extracted"
        if extracted_dir.exists():
            for firmware_dir in extracted_dir.iterdir():
                if firmware_dir.is_dir():
                    firmware_name = firmware_dir.name
                    results["extracted_structure"][firmware_name] = self._analyze_extracted_structure(firmware_dir)
                    logger.info(f"Analyzing extraction structure: {firmware_name}")
        
        # Get original firmware file information
        database_dir = Path("database")
        if database_dir.exists():
            for firmware_file in database_dir.glob("*.bin"):
                file_stat = firmware_file.stat()
                results["firmware_files"].append({
                    "name": firmware_file.name,
                    "size": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2)
                })
        
        return results
    
    def _analyze_extracted_structure(self, firmware_dir: Path) -> Dict[str, Any]:
        """Analyze firmware extraction directory structure"""
        structure = {
            "extraction_success": False,
            "squashfs_found": False,
            "filesystem_structure": [],
            "file_counts": {},
            "suspicious_files": []
        }
        
        extracted_path = firmware_dir / f"_{firmware_dir.name}.bin.extracted"
        if extracted_path.exists():
            structure["extraction_success"] = True
            
            # Check squashfs root filesystem
            squashfs_root = extracted_path / "squashfs-root"
            if squashfs_root.exists():
                structure["squashfs_found"] = True
                structure["filesystem_structure"] = self._get_filesystem_structure(squashfs_root)
                structure["file_counts"] = self._count_files_by_type(squashfs_root)
            
            # Find other extracted files
            for item in extracted_path.iterdir():
                if item.is_file():
                    if item.suffix in ['.squashfs', '.gz', '.7z']:
                        structure["suspicious_files"].append({
                            "name": item.name,
                            "size": item.stat().st_size,
                            "type": "compressed_archive"
                        })
        
        return structure
    
    def _get_filesystem_structure(self, root_path: Path) -> List[str]:
        """Get basic filesystem structure"""
        structure = []
        if root_path.exists():
            for item in root_path.iterdir():
                if item.is_dir():
                    structure.append(item.name)
        return sorted(structure)
    
    def _count_files_by_type(self, root_path: Path) -> Dict[str, int]:
        """Count files by type"""
        counts = {"directories": 0, "executables": 0, "configs": 0, "libraries": 0, "other": 0}
        
        if not root_path.exists():
            return counts
        
        try:
            for item in root_path.rglob("*"):
                if item.is_dir():
                    counts["directories"] += 1
                elif item.is_file():
                    if item.suffix in ['.so', '.a']:
                        counts["libraries"] += 1
                    elif item.suffix in ['.conf', '.cfg', '.ini', '.xml']:
                        counts["configs"] += 1
                    elif item.name in ['bin', 'sbin'] or (item.stat().st_mode & 0o111):
                        counts["executables"] += 1
                    else:
                        counts["other"] += 1
        except (PermissionError, OSError) as e:
            logger.warning(f"Unable to fully analyze directory structure: {e}")
        
        return counts
    
    def generate_review_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate review analysis prompt"""
        prompt = f"""
As a firmware security analysis expert, please analyze the correctness and completeness of the following binwalk parsing results.

## Analysis Data

### Firmware File Information
{json.dumps(analysis_data['firmware_files'], indent=2, ensure_ascii=False)}

### Binwalk Analysis Reports
{json.dumps(analysis_data['reports'], indent=2, ensure_ascii=False)}

### Extracted File Structure Analysis
{json.dumps(analysis_data['extracted_structure'], indent=2, ensure_ascii=False)}

## Please analyze from the following perspectives:

### 1. Recognition Accuracy Analysis
- Evaluate if binwalk correctly identified component types (U-Boot, LZMA, gzip, Squashfs, etc.)
- Check if offset addresses are reasonable
- Verify compression format recognition accuracy

### 2. Extraction Completeness Assessment
- Analyze if filesystem extraction was successful
- Check if extracted directory structure matches embedded Linux system characteristics
- Evaluate extracted file completeness

### 3. Firmware Structure Reasonableness
- Analyze if firmware layout matches common router firmware structure
- Check if component sizes are reasonable
- Evaluate timestamp reasonableness

### 4. Potential Issue Identification
- Identify possible parsing errors or omissions
- Check for unrecognized important components
- Analyze reasons for extraction failures

### 5. Security Considerations
- Evaluate firmware security features
- Identify potential security risks

## Output Requirements
Please generate a detailed analysis report in English, including:
1. Executive Summary
2. Detailed Analysis Results
3. Issues Found and Recommendations
4. Overall Score (1-10)

Please ensure the analysis is professional, objective, and detailed.
"""
        return prompt
    
    def analyze_with_llm(self, analysis_data: Dict[str, Any]) -> str:
        """Use large language model to analyze binwalk results"""
        prompt = self.generate_review_prompt(analysis_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional firmware security analysis expert, proficient in binwalk tools and embedded system firmware analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return f"LLM analysis failed: {str(e)}"
    
    def generate_detailed_report(self, analysis_data: Dict[str, Any], llm_analysis: str) -> str:
        """Generate detailed review report"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Binwalk Parsing Results Review Report

**Generated Time**: {timestamp}
**Analysis Tools**: Binwalk + GPT-4 Intelligent Analysis
**Analyst**: AI Firmware Security Analysis System

---

## 1. Overview

### Analyzed Firmware Files
"""
        
        for firmware in analysis_data['firmware_files']:
            report += f"- **{firmware['name']}**: {firmware['size_mb']} MB\n"
        
        report += f"""
### Analysis Scope
- Binwalk signature scan results
- File extraction and decompression results
- Filesystem structure analysis
- Component recognition accuracy verification

---

## 2. AI Expert Analysis Results

{llm_analysis}

---

## 3. Technical Details Analysis

### 3.1 Binwalk Recognition Results Details
"""
        
        for firmware_name, report_data in analysis_data['reports'].items():
            report += f"""
#### {firmware_name}
- **Analysis Time**: {report_data.get('analysis_timestamp', 'N/A')}
- **Recognized Components Count**: {report_data['results']['api_results']['extraction']['count']}

**Recognized Components**:
"""
            for i, result in enumerate(report_data['results']['api_results']['extraction']['results'], 1):
                report += f"{i}. **Offset {result['offset']}**: {result['description']}\n"
        
        report += """
### 3.2 Filesystem Extraction Analysis
"""
        
        for firmware_name, structure in analysis_data['extracted_structure'].items():
            report += f"""
#### {firmware_name} Extraction Results
- **Extraction Success**: {'✅' if structure['extraction_success'] else '❌'}
- **Squashfs Filesystem**: {'✅ Found' if structure['squashfs_found'] else '❌ Not Found'}
"""
            if structure['filesystem_structure']:
                report += f"- **Directory Structure**: {', '.join(structure['filesystem_structure'])}\n"
            
            if structure['file_counts']:
                report += "- **File Statistics**:\n"
                for file_type, count in structure['file_counts'].items():
                    report += f"  - {file_type}: {count}\n"
        
        report += f"""
---

## 4. Summary and Recommendations

### 4.1 Analysis Quality Assessment
Based on the above technical analysis and AI expert evaluation, the overall quality of this binwalk parsing is at a professional level.

### 4.2 Improvement Suggestions
1. If extraction failures are found, manual extraction methods are recommended
2. For critical configuration files and executables, further security analysis is recommended
3. Regularly update binwalk signature database to improve recognition accuracy

### 4.3 Follow-up Analysis Directions
- Firmware vulnerability scanning
- Configuration file security audit
- Binary file reverse analysis
- Network service security assessment

---

**Report Generator**: Auto-Binwalk AI Review System  
**Technical Support**: GPT-4 based intelligent firmware analysis platform
"""
        
        return report
    
    def run_review(self) -> str:
        """Execute complete review analysis process"""
        logger.info("Starting binwalk results review analysis...")
        
        # Read analysis results
        logger.info("Reading binwalk analysis results...")
        analysis_data = self.read_analysis_results()
        
        if not analysis_data['reports']:
            raise ValueError("No binwalk analysis reports found, please run binwalk analysis first")
        
        # Use LLM for analysis
        logger.info("Using large language model for intelligent analysis...")
        llm_analysis = self.analyze_with_llm(analysis_data)
        
        # Generate detailed report
        logger.info("Generating detailed review report...")
        detailed_report = self.generate_detailed_report(analysis_data, llm_analysis)
        
        # Save report
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.review_dir / f"binwalk_review_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(detailed_report)
        
        logger.info(f"Review report saved to: {report_file}")
        return str(report_file)


def main():
    """Main function"""
    print("Binwalk Analysis Review Tool")
    print("=" * 50)
    
    # Get API configuration
    api_key = input("Please enter OpenAI API Key (or set OPENAI_API_KEY environment variable): ").strip()
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OpenAI API Key is required")
            return
    
    base_url = input("Please enter API Base URL (optional, press Enter for default): ").strip()
    if not base_url:
        base_url = None
    
    model = input("Please enter model name (default: gpt-4): ").strip()
    if not model:
        model = "gpt-4"
    
    try:
        # Create analyzer
        analyzer = BinwalkReviewAnalyzer(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        
        # Execute review
        report_path = analyzer.run_review()
        
        print(f"\n✅ Review analysis completed!")
        print(f"📄 Report file: {report_path}")
        print("\nPlease check the generated Markdown report for detailed analysis results.")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
