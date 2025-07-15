
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel


router = APIRouter()

class inputPathRequest(BaseModel):
    input: str

@router.post("/ai/", tags=["ai"])
def get_file_ai(input_path : inputPathRequest):
    """
    AI 분석 결과 저장
    INPUT : 정제된 텍스트 파일 경로
    OUTPUT : AI 결과 파일 경로
    """
    aa = AiAnalysis(input_path.input)
    aa.split_file()
    #aa.check_chunks()
    aa.execute_gpt()
    aa.record_analysis()
    folder_path = aa.return_unique_id()
    return JSONResponse(content = {"folder_path":folder_path})


import os
import time
from openai import OpenAI

class AiAnalysis:
    def __init__(self, input_path):
        self.input_path = f"{input_path}/combined.txt"
        self.output_path = f"{input_path[:-2]}#2"
        self.INPUT_TOKEN = 5000
        self.chunks = []
        self._api_key = 
        self.api_key = 


    def split_file(self):
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"{self.input_path}는 존재하지 않는 경로입니다")
        with open(self.input_path, "r", encoding="UTF-8")as f:
            js_content = f.read()
        print(f"읽은 파일 크기: {len(js_content)} bytes")
        for i in range(0, len(js_content), self.INPUT_TOKEN):
            self.chunks.append(js_content[i : i+self.INPUT_TOKEN])
        
        print(f"{len(self.chunks)}개의 조각으로 분활 완료")

    def check_chunks(self):
        # 디버깅용 분활 확인 함수
        for idx, chunk in enumerate(self.chunks, 1):
            print(f"utf-8인코딩 글자수 : {len(chunk.encode("utf-8"))}")
            char_len = len(chunk)
            byte_len = len(chunk.encode("utf-8"))
            print(f"{idx}번째 chunk: {char_len} chars / {byte_len} bytes")
            print(chunk)

    def execute_gpt(self):
        client = OpenAI(api_key=self.api_key)

        for index, chunk in enumerate(self.chunks, 1):
            print(f"[{index}/{len(self.chunks)}] 조각 분석 중")
            meaningful_result = ""

            for tries in range(2): # 이중 분석
                for retries in range(3): # 1,2,4초 대기 후 시도
                    try:

                        response = client.chat.completions.create(
                            model="gpt-4.1-mini",
                            messages=[
                                {
                                    "role": "system", "content": """ 당신은 사이버 보안 전문가입니다. 입력받은 코드 내에 크립토재킹과 관련된 위험 요소가 **실제로 존재할 경우에만**, 이를 탐지하고 반드시 JSON 형식으로 출력하세요.
                                                1. 크립토재킹 요소가 있으면 다음과 같이 JSON형태로 출력하기
                                                {
                                                    "cryptojacking element": " 이곳에 크립토재킹 요소에 해당하는 코드 그대로 작성"
                                                }
                                                2. 만약 크립토재킹 요소인데, 난독화 되어있다면 난독화를 해제 후 평문을 출력해주세요.
                                                3. 크립토재킹 요소가 없으면 '{}'만 출력하기
                                                4. 해설이나 설명은 절대 쓰지 않기"""
                                },
                                {"role": "user", "content": chunk}
                            ]
                        )

                        content = response.choices[0].message.content

                        if content.strip(): # 성공했고, 내용도 있으면
                            print(f"    [시도 {tries+1}] 분석 성공")
                            meaningful_result = content
                            break
                        else: # 성공했는데, 내용이 없으면 재시도
                            raise Exception

                    except Exception as e:
                        print(f"    [시도 {tries+1}] 분석 실패 (재시도 {retries+1}): {e}")
                        wait = 2 ** retries
                        print(f"    **{wait}초 대기 후 재시도**")
                        time.sleep(wait)
                
                # 에러메시지가 아닌 정상적인 response가 담긴다면 조각 분석 완료
                if meaningful_result:
                    break
            
            # 이중 분석이 모두 완료되고, 여전히 에러 메시지만 존재한다면 빈 json만
            self.final_result.append(meaningful_result or "{}")

    def record_analysis(self): # 위 함수와 합치거나
        os.mkdir(self.output_path)
        with open(f"{self.output_path}/ai_analysis.txt", "w", encoding="utf-8") as f:
            for idx, res in enumerate(self.final_result, 1):
                f.write(f"\n[조각 {idx} 결과]\n{res}\n")
        print(f"AI 분석 결과가 저장되었습니다: {self.output_path}/ai_analysis.txt")

    def return_unique_id(self):
        return self.output_path
