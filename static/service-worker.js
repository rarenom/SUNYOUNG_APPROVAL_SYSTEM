// ==========================
// SUNYOUNG PWA Service Worker
// ==========================


// 설치
self.addEventListener("install", function(event){

    console.log("SUNYOUNG APP 설치 완료");

    self.skipWaiting();

});




// 활성화
self.addEventListener("activate", function(event){

    console.log("SUNYOUNG APP 활성화");

    event.waitUntil(

        self.clients.claim()

    );

});




// 페이지 요청 처리
self.addEventListener("fetch", function(event){

});




// ==========================
// 푸시 알림 수신
// ==========================

self.addEventListener("push", function(event){


    console.log(
        "푸시 데이터 수신"
    );



    let data = {};



    if(event.data){


        try{


            data = event.data.json();


        }

        catch(e){


            data = {

                body:event.data.text()

            };


        }

    }




    const title =

        data.title

        ||

        "SUNYOUNG ERP";





    const options = {



        body:

        data.body

        ||

        "새로운 알림이 있습니다.",




        icon:

        "/static/icon.png",




        badge:

        "/static/icon.png",




        vibrate:[

            200,

            100,

            200

        ],




        data:{


            url:"/main"


        }



    };






    event.waitUntil(


        self.registration.showNotification(

            title,

            options

        )


    );


});







// ==========================
// 알림 클릭
// ==========================

self.addEventListener(

"notificationclick",

function(event){



    console.log(

        "알림 클릭"

    );



    event.notification.close();





    event.waitUntil(



        clients.matchAll({


            type:"window",


            includeUncontrolled:true


        })



        .then(function(clientList){





            for(

                const client of clientList

            ){



                if(

                    client.url.includes(

                    "sunyoung-approval-system.onrender.com"

                    )

                ){



                    return client.focus();



                }


            }





            return clients.openWindow(

                event.notification.data.url

            );




        })



    );



}

);