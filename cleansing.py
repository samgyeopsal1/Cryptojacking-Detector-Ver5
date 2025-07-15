from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse


router = APIRouter()

class inputPathRequest(BaseModel):
    input: str

@router.post("/cleansing/", tags=["cleansing"])
def get_resources(input_path: inputPathRequest):
    """
    리소스에서 유의미한 JavaScript 추출
    INPUT : 리소스 저장 폴더 경로
    OUTPUT : 정제된 텍스트 파일 경로
    """
    
    dc = DataCleansing(input_path.input)
    dc.get_hidden_code()
    dc.get_executable_code()
    dc.make_file()
    dc.remove_resources()
    folder_path = dc.return_unique_id()

    return JSONResponse(content={"folder_path":folder_path})    


import os
import re
import shutil
from PIL import Image

class DataCleansing:
    def __init__(self, input_path):
        self.input_path = input_path
        self.report = []
        self.js_content = []
        self.output_path =f"{self.input_path[:-2]}#1"

    def get_hidden_code(self):
        self.report = []
        def extract_message(img):
            binary_str = ""
            for pixel in img.getdata():
                for channel in pixel[:3]:  
                    binary_str += str(channel & 1)
            
            byte_arr = []
            for i in range(0, len(binary_str), 8):
                byte = binary_str[i:i+8]
                if len(byte) < 8:
                    continue
                value = int(byte, 2)
                if value == 0:  
                    break
                byte_arr.append(value)
            
            try:
                return bytes(byte_arr).decode('utf-8', errors='ignore') 
            except UnicodeDecodeError:
                return ''
        
        for fname in os.listdir(self.input_path):
            fpath = os.path.join(self.input_path, fname)
            if not os.path.isfile(fpath):
                continue
            if fname.split('.')[-1].lower() not in ["png", "jpg"]:
                continue
            try:
                img = Image.open(fpath)
                hidden_msg = extract_message(img)
                if hidden_msg.strip():
                    self.report.append(f"\n// ==== {fname} ====\n\n{hidden_msg}")
            except Exception as e:
                print(f"{fname}에서 오류 발생: {e}")
        print(f"스테가노그래피 메시지 {len(self.report)}개 추출 완료")
        return self.report

    def get_executable_code(self):
        seen = set()
        js_patterns = [
            r'<script[^>]*>(.*?)</script>',
            r'<script\s+[^>]*src\s*=\s*["\'](.*?)["\']',
            r'<iframe\s+[^>]*src\s*=\s*["\'](.*?)["\']',
            r'<iframe[^>]*>(.*?)</iframe>',
            r'(?:function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}' +
            r'|(?:var|let|const)\s+\w+\s*=\s*[^;]+;' +
            r'|[\w.]+\s*=\s*function[^}]*\})'
        ]
        
        for fname in os.listdir(self.input_path):
            fpath = os.path.join(self.input_path, fname)
            
            if not os.path.isfile(fpath): continue
            if fname.split('.')[-1].lower() in ["png", "jpg"]: continue
            
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f"{fname} 파일 열기 실패: {e}")
            
            unique_blocks = []
            for pattern in js_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                for block in matches:
                    block = block.strip()
                    if block and block not in seen:
                        seen.add(block)
                        unique_blocks.append(block)
            
            if unique_blocks:
                self.js_content.append(f"\n// ==== {fname} ====\n"+"\n".join(unique_blocks))
        print(f"JS 블록 {len(self.js_content)}개 추출 완료")
        return self.js_content

    def make_file(self):
        os.mkdir(self.output_path)
        with open(f"{self.output_path}/combined.txt", "w", encoding="utf-8") as f:
            f.write("// ==== 스테가노그래피로 은닉된 코드 ====\n")
            f.write("".join(self.report))
            
            f.write("\n// ==== 추출된 JavaScript 코드 ====\n")
            f.write("".join(self.js_content))
        
        print(f"추출된 전체 블록 개수 : {len(self.report)+len(self.js_content)}")
        print(f"정제가 완료되었습니다: {self.output_path}/combined.txt")

    def remove_resources(self):
        if os.path.isdir(self.input_path):
            try:
                shutil.rmtree(self.input_path)
                print(f"폴더 제거 완료: {self.input_path}")
            except: pass

    def return_unique_id(self):
        return self.output_path
