// ==================================
// SUNYOUNG ERP PWA SERVICE WORKER
// ==================================


self.addEventListener(
"install",
function(event){

    console.log(
        "SUNYOUNG PWA 설치 완료"
    );


    self.skipWaiting();

});



self.addEventListener(
"activate",
function(event){

    console.log(
        "SUNYOUNG PWA 활성화"
    );


    event.waitUntil(
        self.clients.claim()
    );

});



self.addEventListener(
"fetch",
function(event){

    // 현재는 캐시 사용 안함
    // Firebase Push와 충돌 방지

});