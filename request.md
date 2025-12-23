1. 대시보드 - 설정
API키 : 입력이 되면 키 필드에 값을 보여줘

2. 대시보드 - 설정
관심 코인 : 콤보박스로 사용자가 선택할 수 있게 하고 코인을 검색할 수 있게 해줘

3. 대시보드 - 설정
알림 : 실제 구현 여부 검증

4. 대시보드 - 요금제
프리 : 급등 모니터링을 급등 알림으로 바꾸고 지원 안하는 걸로 변경
베이식 : 자동매매 알림 주 3회를 급등알림 주 최소 3회로 변경
프로 : 자동매매 알림 주 10회를 급등알림 주 최소 10회로 변경

급등알림이 발생하지 않을 경우의 면책조항도 추가해줘.


5. 대시보드 - 친구 초대하기
내 추천 코드 : 로딩중 
최근 초대 내역 : 로딩중
구현기능 검증해줘

6. 대시보드 - 텔레그램 연동
연동 상태에
오류: File not found 나오고 있고 
api/admin/api/telegram/link/status:1  Failed to load resource: the server responded with a status of 404 (NOT FOUND)

텔레그램 연동 설정이 필요한가?

7. 대시보드 - 내 시그널
requests.js:1  GET https://coinpulse.sinsi.ai/api/admin/api/user/signals/stats 404 (NOT FOUND)
(anonymous) @ requests.js:1
(anonymous) @ traffic.js:1
fetch @ traffic.js:1
loadStats @ VM1842:32
loadData @ VM1842:25
init @ VM1842:19
(anonymous) @ VM1842:209
(anonymous) @ VM1842:210
executeScripts @ page-loader.js:155
loadPage @ page-loader.js:79
loadExternalPage @ dashboard.html:1642
handleNavigation @ dashboard.html:1726
requests.js:1  GET https://coinpulse.sinsi.ai/api/admin/api/user/signals?status=all&limit=50 404 (NOT FOUND)
(anonymous) @ requests.js:1
(anonymous) @ traffic.js:1
fetch @ traffic.js:1
loadSignals @ VM1842:62
loadData @ VM1842:26
init @ VM1842:19
(anonymous) @ VM1842:209
(anonymous) @ VM1842:210
executeScripts @ page-loader.js:155
loadPage @ page-loader.js:79
loadExternalPage @ dashboard.html:1642
handleNavigation @ dashboard.html:1726
VM1842:153 Error loading signals: TypeError: Cannot set properties of null (setting 'innerHTML')
    at loadSignals (<anonymous>:72:41)
    at async Promise.all (index 1)
    at async loadData (<anonymous>:24:13)
    at async init (<anonymous>:19:13)
loadSignals @ VM1842:153
await in loadSignals
loadData @ VM1842:26
init @ VM1842:19
(anonymous) @ VM1842:209
(anonymous) @ VM1842:210
executeScripts @ page-loader.js:155
loadPage @ page-loader.js:79
loadExternalPage @ dashboard.html:1642
handleNavigation @ dashboard.html:1726
VM1842:154 Uncaught (in promise) TypeError: Cannot set properties of null (setting 'innerHTML')
    at loadSignals (<anonymous>:154:66)
    at async Promise.all (index 1)
    at async loadData (<anonymous>:24:13)
    at async init (<anonymous>:19:13)
loadSignals @ VM1842:154
await in loadSignals
loadData @ VM1842:26
init @ VM1842:19
(anonymous) @ VM1842:209
(anonymous) @ VM1842:210
executeScripts @ page-loader.js:155
loadPage @ page-loader.js:79
loadExternalPage @ dashboard.html:1642
handleNavigation @ dashboard.html:1726

8. 대시보드 - 급등 예측
급등 예측 모니터링을 하고 있나?
유효한 정보가 하나도 없어...
"내 시그널"과는 별개인가?
"내 시그널"은 뭐지?

8. 대시보드 - 자동 거래
ln9swrd@gmail.com 베이식 요금제 인데
요금제 업그레이드가 보이네...


9. 대시보드 - 거래 내역
오류 발생....
dashboard-fixed.js?v=20251221_auto_fixed:690 Error loading order history: TypeError: Cannot read properties of undefined (reading 'getToken')
    at DashboardManager.loadOrderHistory (dashboard-fixed.js?v=20251221_auto_fixed:599:62)
    at dashboard-fixed.js?v=20251221_auto_fixed:579:35
loadOrderHistory @ dashboard-fixed.js?v=20251221_auto_fixed:690
(anonymous) @ dashboard-fixed.js?v=20251221_auto_fixed:579
setTimeout
loadHistoryPage @ dashboard-fixed.js?v=20251221_auto_fixed:579
loadPage @ dashboard-fixed.js?v=20251221_auto_fixed:204
(anonymous) @ dashboard-fixed.js?v=20251221_auto_fixed:135

10. 대시보드 - 포트폴리오
로딩 속도를 더 빨리해줘

11. 대시보드 - 거래 차트
수동 주문 기능이 제대로 구현되었는지 검증해줘
xrp에 매도 주문이 있는데 그 주문을 차트에서 드래그해서 가격을 변경하는 것과
주문을 선택해서 취소하는 기능을 구현해줘


12. 대시보드 -  잘 나오던 페이지도 다시 클릭해서 이동하면 Page not found가 보여 자주