from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter()

class inputPathRequest(BaseModel):
    input: str

@router.post("/signature/", tags=["signature"])
def get_file_sg(input_path: inputPathRequest):
    """
    시그니처 분석 결과 저장
    INPUT : 정제된 텍스트 파일 경로
    OUTPUT : 시그니처 결과 파일 경로
    """
    sa = SignatureAnalysis(input_path.input)
    sa.check_pattern()
    sa.make_file()
    folder_path = sa.return_filepath()
    print(folder_path)

    return JSONResponse(content={"folder_path":folder_path})

import os
import re
import json

class SignatureAnalysis:
    def __init__(self, input_path):
        self.input_path = f"{input_path}/combined.txt"
        self.output_path = f"{input_path[:-2]}#3"
        self.result = []
    
    def check_pattern(self):
        PATTERNS = [
            r'deepminer', r'webminepool', r'monero', r'webminer',
            r'mining', r'moneroocean', r'walletAddress', r'workerId',
            r'startMining', r'throttleMiner'
        ]
        with open(self.input_path, "r", encoding="utf-8")as f:
            content = f.read()
        
        for pattern in PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            if matches:
                self.result.append((pattern, len(matches)))
    
    def make_file(self):
        os.mkdir(self.output_path)
        
        json_result = [{"signature": pattern, "count": hit_count} for pattern, hit_count in self.result]
        with open(f"{self.output_path}/signature_analysis.txt", "w", encoding="utf-8")as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
            print(f"시그니처 분석 결과가 저장되었습니다: {self.output_path}/signature_analysis.txt")
    
    def return_filepath(self):
        return self.output_path