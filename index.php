<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Cryptojacking Detector</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Cryptojacking Detector</h1>
    <h6>쉽고 빠르게 당신의 컴퓨터 리소스를 보호하세요</h6>
    <form method="post" autocomplete="off">
        <input type="text" name="siteUrl" placeholder="검사하고 싶은 사이트의 주소를 입력하세요" size="50" required>
        <button type="submit">검색</button>
    </form>

    <div id="log">

    <?php
    ini_set('output_buffering', 'off');
    ini_set('zlib.output_compression', false);
    header('Content-Encoding: none');
    ob_implicit_flush(1);
    while (ob_get_level() > 0) {
        ob_end_flush();
    }
    echo str_repeat(' ', 1024); 
    flush();
    if ($_SERVER["REQUEST_METHOD"] === "POST" && !empty($_POST["siteUrl"])) {
        $siteUrl = trim($_POST["siteUrl"]);
        
        echo "\n리소스 다운로드 중...";
        @flush();
        if (!filter_var($siteUrl, FILTER_VALIDATE_URL)) {
            echo "\n유효한 URL 형식이 아닙니다.";
            if (ob_get_length()) { ob_flush(); flush(); }
            exit;
        }


        // 1단계
        $urlApi = 
        $urlData = ['siteUrl' => $siteUrl];
        $ch1 = curl_init($urlApi);
        curl_setopt($ch1, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch1, CURLOPT_POST, true);
        curl_setopt($ch1, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch1, CURLOPT_POSTFIELDS, json_encode($urlData));
        $urlResponse = curl_exec($ch1);
        if (curl_errno($ch1)) {
            echo '\nURL 입력과정에서 오류가 발생했습니다: ' . curl_error($ch1);
            @flush();
            curl_close($ch1);
            exit;
        }
        curl_close($ch1);
        $parsedFolder = json_decode($urlResponse, true);
        if (!isset($parsedFolder['folder_name'])) {
            echo '\n유효한 폴더 경로를 받지 못했습니다.';
            @flush();
            exit;
        }
        $folder_path = $parsedFolder['folder_name'];
        echo "\n[1] 리소스가 정상적으로 다운로드되었습니다.";
        echo "\n\n데이터 정제 중...";
        @flush();


        // 2단계
        $cleansingApi = 
        $cleansingData = ['input' => $folder_path];
        $ch2 = curl_init($cleansingApi);
        curl_setopt($ch2, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch2, CURLOPT_POST, true);
        curl_setopt($ch2, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch2, CURLOPT_POSTFIELDS, json_encode($cleansingData));
        $cleansingResponse = curl_exec($ch2);
        if (curl_errno($ch2)) {
            echo '\n데이터 정제과정에서 오류가 발생했습니다:' . curl_error($ch2);
            @flush();
            curl_close($ch2);
            exit;
        }
        curl_close($ch2);
        $cleansingPath = json_decode($cleansingResponse, true);
        if (!$cleansingPath) {
            echo '\n정제된 JS 파일 경로가 유효하지 않습니다.\n';
            @flush();
            exit;
        }
        $cleanFolder = json_decode($cleansingResponse, true);
        $cleanPath = $cleanFolder['folder_path'] ?? null;
        echo "\n[2] 데이터 정제가 완료되었습니다.\n";
        echo "\n\nAI 분석 중...";
        @flush();


        // 3단계
        $aiApi = 
        $aiData = ['input' => $cleanPath];
        $ch3 = curl_init($aiApi);
        curl_setopt($ch3, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch3, CURLOPT_POST, true);
        curl_setopt($ch3, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch3, CURLOPT_POSTFIELDS, json_encode($aiData));
        $aiResponse = curl_exec($ch3);
        if (curl_errno($ch3)) {
            echo ': ' . curl_error($ch3);
            curl_close($ch3);
            exit;
        }
        curl_close($ch3);
        $aiParsed = json_decode($aiResponse, true);
        $aiPath = $aiParsed['folder_path'] ?? null;
        @flush();
        echo "\n[3] AI 분석이 완료되었습니다.\n";
        echo "\n\n시그니처 분석 중 ...";
        @flush();


        // 4단계
        $sgApi = 
        $sgData = ['input' => $cleanPath];
        $ch4 = curl_init($sgApi);
        curl_setopt($ch4, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch4, CURLOPT_POST, true);
        curl_setopt($ch4, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch4, CURLOPT_POSTFIELDS, json_encode($sgData));
        $sgResponse = curl_exec($ch4);
        if (curl_errno($ch4)) {
            echo '\nAI 분석과정에서 오류가 발생했습니다: ' . curl_error($ch4);
            @flush();
            curl_close($ch4);
            exit;
        }
        curl_close($ch4);
        $sgParsed = json_decode($sgResponse, true);
        $sgPath = $sgParsed['folder_path'] ?? null;
        echo "\n[4] 시그니처 분석이 완료되었습니다.\n";
        echo "\n\n결과 종합 중...";
        @flush();


        // 5단계
        $resultApi =
        $resultData = ['input1' => $aiPath, 'input2' => $sgPath];
        $ch5 = curl_init($resultApi);
        curl_setopt($ch5, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch5, CURLOPT_POST, true);
        curl_setopt($ch5, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch5, CURLOPT_POSTFIELDS, json_encode($resultData));
        $resultResponse = curl_exec($ch5);
        if (curl_errno($ch5)) {
            echo '\n결과 제공과정에서 오류가 발생했습니다: ' . curl_error($ch5);
            @flush();
            curl_close($ch5);
            exit;
        }
        curl_close($ch5);
        $resultParsed = json_decode($resultResponse, true);
        $resultPath = $resultParsed['risk_level'] ?? null;
        echo "\n분석이 모두 완료되었습니다";
        echo "\n\n$resultPath\n";
        flush();
    }
    ?>
    </div>
</body>
</html>

