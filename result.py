from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter()

class inputPathRequest(BaseModel):
    input1: str
    input2: str

@router.post("/result/", tags=["result"])
def get_analysis(payload: inputPathRequest):
    """
    탐지 결과 반환
    INPUT : AI 결과 파일 경로, 시그니처 결과 파일 경로
    OUTPUT : 탐지 결과 텍스트
    """
    sr = ShowResult(payload.input1, payload.input2)
    sr.check_ai()
    sr.check_sg()
    sr.make_file()
    a, s = sr.return_result()
    print(f"ai_cnt : {a}, signature_cnt : {s}")
    risk_level = sr.print_result()
    sr.show_result()
    return JSONResponse(content={"risk_level":risk_level})

import re
import os
import json

class ShowResult:
    def __init__(self, input_path_ai, input_path_sg):
        self.input_path_1 = f"{input_path_ai}/ai_analysis.txt"
        self.input_path_2 = f"{input_path_sg}/signature_analysis.txt"
        self.output_path = f"{input_path_ai[:-2]}#4"
        self.extracted = []
        self.data = []

    def check_ai(self):
        with open(self.input_path_1, "r", encoding="utf-8")as f:
            content = f.read()
        
        # [조각 n 결과] 기준으로 chunk를 나누고 split_chunks에 리스트로 저장
        split_chunks = re.split(r"(?=\[조각 \d+ 결과\])", content)
        for chunk in split_chunks:
            chunk = chunk.strip()
            
            if not chunk:
                continue
            
            # {...} 형태가 아니면 제외 
            if not re.fullmatch(r"^\[조각 \d+ 결과\]\s*\{.*\}\s*$", chunk, re.DOTALL):
                continue
            
            # 제외할 형태 패턴 정의
            exclude_patterns = [
                r"\[조각 \d+ 결과\]\s*```json\s*\[\]\s*```",                               # [조각 n 결과] ```json [] ``` 제외
                r"\[조각 \d+ 결과\]\s*```json\s*\{\}\s*```",                               # [조각 n 결과] ```json {} ``` 제외
                r"\[조각 \d+ 결과\]\s*\{\}",                                               # [조각 n 결과] {} 제외
                r"\[조각 \d+ 결과\]\s*\[\]",                                               # [조각 n 결과] [] 제외
                r"\[조각 \d+ 결과\]\s*[^\{\[\n]+",                                         # [조각 n 결과] "줄글" 제외
                r"\[조각 \d+ 결과\]\s*\{\s*\"cryptojacking_element\"\s*:\s*\[\s*\]\s*\}",  # [조각 n 결과] {"cryptojacking_element" : []} 제외
                r"\[조각 \d+ 결과\]\s*\{\s*\"cryptojacking_element\"\s*:\s*\"\"\s*\}"     # [조각 n 결과] {"cryptojacking_element" : ""} 제외
            ]
            
            if any(re.fullmatch(pattern, chunk, re.DOTALL) for pattern in exclude_patterns):
                continue
            
            # ```json ... ``` 내부만 추출
            code_block_match = re.search(r"\[조각 \d+ 결과\]\s*```json\s*(.*?)\s*```", chunk, re.DOTALL)
            if code_block_match:
                json_body = code_block_match.group(1).strip()
                self.extracted.append(json_body)
                continue
            
            # 그냥 JSON 본문만 있는 경우
            inline_match = re.match(r"\[조각 \d+ 결과\]\s*(\{.*\}|\[.*\])", chunk, re.DOTALL)
            if inline_match:
                json_body = inline_match.group(1).strip()
                self.extracted.append(json_body)
                continue
                
            match = re.match(r"\[조각 \d+ 결과\]\s*(.*)", chunk, re.DOTALL) # [조각 n 결과] 부분만
            if match:
                json_body = match.group(1).strip() # 그 뒷부분 {..}만 추출
                self.extracted.append(json_body)
        print(f"AI분석 탐지 개수: {len(self.extracted)}")

    def check_sg(self):
        with open(self.input_path_2, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        print(f"시그니처 탐지 개수: {len(self.data)}")

    def make_file(self):
        os.mkdir(self.output_path)
        with open(f"{self.output_path}/final.txt", "w", encoding="utf-8") as f:
            for result1 in self.extracted: 
                f.write(result1+"\n\n")
            f.write("\n")
            
            with open(self.input_path_2, "r", encoding="utf-8") as file:
                result2 = file.read()
            f.write(result2 + "\n\n")
        
        print(f"최종 분석 파일이 저장되었습니다: {self.output_path}/final.txt")

    def return_result(self):
        return len(self.extracted), len(self.data)

    def print_result(self):
        print("\n[최종 결과]")
        # 모든 탐지 방법에서 탐지될 경우 : 위험
        if len(self.extracted)>=1 and len(self.data)>=1:
            result = f"🔴 [위험] cryptojacking 시도 중인 사이트입니다. 🔴\n AI 정적분석에서 {len(self.extracted)}개, 시그니처 기반 정적분석에서 {len(self.data)}개의 위험요소가 발견되었습니다.\n"
            content = self.show_result()
            return result + content
        # 한 가지 탐지 방법에서만 탐지될 경우 : 의심
        elif ( len(self.extracted)>=1 and len(self.data)==0) or ( len(self.extracted)==0 and len(self.data)>=1):
            result = f"🟡 [의심] cryptojacking 시도 중인 사이트일 가능성이 높습니다. 🟡\nAI 정적분석에서 {len(self.extracted)}개, 시그니처 기반 정적분석에서 {len(self.data)}개의 위험요소가 발견되었습니다."
            content = self.show_result()
            return result + content
        # 모든 탐지 방법에서 탐지되지 않은 경우 : 안전
        elif len(self.extracted)==0 and len(self.data)==0:
            result = f"🟢 [안전] 감지된 cryptojacking 요소가 없습니다. 🟢\nAI 정적분석에서 {len(self.extracted)}개, 시그니처 기반 정적분석에서 {len(self.data)}개의 위험요소가 발견되었습니다."
            content = self.show_result()
            return result + content

    def show_result(self):
        with open(f"{self.output_path}/final.txt", "r", encoding="utf-8") as f:
            content = f.read()
        return content
