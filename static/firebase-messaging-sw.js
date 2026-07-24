// ==================================
// FIREBASE CLOUD MESSAGE SERVICE WORKER
// ==================================


importScripts(
"https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"
);


importScripts(
"https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js"
);



firebase.initializeApp({

    apiKey:
    "AIzaSyAMMkwzgYJXT6iKP0WVNT6HSUMAy9Imw0",


    authDomain:
    "sunyoung-erp-push.firebaseapp.com",


    projectId:
    "sunyoung-erp-push",


    storageBucket:
    "sunyoung-erp-push.firebasestorage.app",


    messagingSenderId:
    "1055876715145",


    appId:
    "1:1055876715145:web:f073ec7cef610fd830ac58"

});



const messaging = firebase.messaging();




// ==================================
// 백그라운드 푸시 수신
// ==================================

messaging.onBackgroundMessage(

function(payload){


    console.log(
        "FCM 백그라운드 수신",
        payload
    );



    let title =
        "선영알림";


    let body =
        "새로운 알림이 있습니다.";



    if(payload.data){


        if(payload.data.title){

            title =
            payload.data.title;

        }



        if(payload.data.body){

            body =
            payload.data.body;

        }

    }



    self.registration.showNotification(

        title,


        {


            body:body,


            icon:
            "/static/icon.png",


            badge:
            "/static/icon.png",


            vibrate:
            [
                300,
                100,
                300
            ],



            requireInteraction:
            true,



            data:
            {

                url:
                "https://sunyoung-approval-system.onrender.com/main"

            }

        }


    );


});





// ==================================
// 알림 클릭
// ==================================

self.addEventListener(

"notificationclick",

function(event){


    console.log(
        "알림 클릭"
    );



    event.notification.close();



    event.waitUntil(


        clients.matchAll(

        {

            type:"window",

            includeUncontrolled:true

        }


        )


        .then(

        function(clientList){



            for(
                let client of clientList
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



});
