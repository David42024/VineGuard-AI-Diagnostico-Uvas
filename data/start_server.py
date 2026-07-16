import uvicorn
import sys, os
os.chdir(r"C:\Users\USERJSSV\Downloads\Diagnostico-Uvas-CNN-IA-master")
sys.path.insert(0, r"C:\Users\USERJSSV\Downloads\Diagnostico-Uvas-CNN-IA-master")
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8002, log_level="info")
