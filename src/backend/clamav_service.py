import subprocess
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scan_file(file_path):
    """
    Scan a file using ClamAV command-line scanner.
    Works on Windows, Linux, and Mac.
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"status": "error", "message": "File not found"}
        
        logger.info(f"Scanning file: {file_path}")
        
        # Run clamscan command
        result = subprocess.run(
            ['clamscan', '--no-summary', file_path],
            capture_output=True,
            text=True,
            timeout=60,
            shell=False
        )
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        logger.info(f"ClamAV stdout: {stdout}")
        logger.info(f"ClamAV return code: {result.returncode}")
        
        # ClamAV return codes:
        # 0 = No virus found (clean)
        # 1 = Virus found
        # 2+ = Error
        
        if result.returncode == 0:
            logger.info(" File is clean")
            return {
                "status": "clean",
                "message": "No threats detected"
            }
        
        elif result.returncode == 1:
            # Virus detected
            logger.warning(f" Virus detected: {stdout}")
            
            # Parse virus name from output
            # Format: "path/to/file: VirusName FOUND"
            virus_name = "Unknown malware"
            if "FOUND" in stdout:
                try:
                    # Extract virus name between ':' and 'FOUND'
                    parts = stdout.split(":")
                    if len(parts) >= 2:
                        virus_info = parts[1].replace("FOUND", "").strip()
                        virus_name = virus_info
                except:
                    pass
            
            return {
                "status": "infected",
                "details": {
                    "virus": virus_name,
                    "file": os.path.basename(file_path),
                    "threat_level": "high"
                }
            }
        
        else:
            # Error occurred
            error_msg = stderr if stderr else stdout
            logger.error(f" ClamAV error: {error_msg}")
            return {
                "status": "error",
                "message": f"Scanner error: {error_msg}"
            }
    
    except FileNotFoundError:
        logger.error("clamscan not found - ClamAV not installed or not in PATH")
        return {
            "status": "error",
            "message": "ClamAV not installed or not in PATH"
        }
    
    except subprocess.TimeoutExpired:
        logger.error("Scan timeout")
        return {
            "status": "error",
            "message": "Scan timeout - file may be too large"
        }
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "status": "error",
            "message": f"Scan failed: {str(e)}"
        }


# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test with provided file
        test_file = sys.argv[1]
        if os.path.exists(test_file):
            result = scan_file(test_file)
            print(f"\n Scan Result: {result}\n")
        else:
            print(f" File not found: {test_file}")
    else:
        # Create and test with clean file
        test_file = "test_clean.txt"
        with open(test_file, 'w') as f:
            f.write("This is a clean test file")
        
        print("Testing with clean file...")
        result = scan_file(test_file)
        print(f" Result: {result}\n")
        
        os.remove(test_file)
        
        print("To test with a real file, run:")
        print(f"  python clamav_service.py <filepath>")