\<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>조직도 배치</title>
  <style>
    /* 전체 화면 중앙 정렬 및 기본 스타일 */
    body {
      margin: 0;
      padding: 40px 20px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      box-sizing: border-box;
      background-color: #fcfcfc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* 그리드 컨테이너: 최대 너비 설정 및 가운데 정렬 */
    .organization-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(220px, 1fr));
      gap: 20px 40px;
      width: 100%;
      max-width: 1000px;
      margin: 0 auto;
    }

    /* 각 열 내부 요소 정렬 */
    .column {
      display: flex;
      flex-direction: column;
      align-items: center; /* 카드들을 열 내에서 가운데 정렬 (좌측 정렬을 원하면 flex-start로 변경) */
      gap: 20px;
    }

    /* 박스 카드 스타일 */
    .card {
      width: 100%;
      max-width: 280px;
      padding: 12px 16px;
      background-color: #ffffff;
      border: 1px dashed #b0c4de;
      border-radius: 8px;
      text-align: center;
      font-size: 14px;
      color: #333333;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
      box-sizing: border-box;
    }
  </style>
</head>
<body>

  <div class="organization-grid">
    <!-- 1열 -->
    <div class="column">
      <div class="card">지휘반 (안전환경팀)</div>
      <div class="card">훈련 및 소화반 (기계팀, 운영팀)</div>
      <div class="card">피난유도반 (계전팀)</div>
    </div>

    <!-- 2열 -->
    <div class="column">
      <div class="card">비상연락반 (조직문화팀)</div>
      <div class="card">경계반 (기획재무팀, DX혁신팀)</div>
    </div>

    <!-- 3열 -->
    <div class="column">
      <div class="card">의료반 (ESG추진팀, 대외협력팀)</div>
      <div class="card">후송반 (고객지원팀)</div>
      <div class="card">방호조치 및 복구반 (네트워크팀)</div>
    </div>
  </div>

</body>
</html>
