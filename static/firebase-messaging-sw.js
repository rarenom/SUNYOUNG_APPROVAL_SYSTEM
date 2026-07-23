importScripts(
"https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"
);

importScripts(
"https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js"
);



firebase.initializeApp({

    apiKey: "AIzaSyAMMkwzgYJXT6iKP0WvNT6HSUMAy9Imw0",

    authDomain: "sunyoung-erp-push.firebaseapp.com",

    projectId: "sunyoung-erp-push",

    storageBucket: "sunyoung-erp-push.firebasestorage.app",

    messagingSenderId: "1055876715145",

    appId: "1:1055876715145:web:f073ec7cef610fd830ac58"

});



const messaging = firebase.messaging();



// ==========================
// 백그라운드 푸시 수신
// ==========================

messaging.onBackgroundMessage(function(payload){


    console.log(
        "백그라운드 메시지:",
        payload
    );



    const title =

        payload.data?.title

        ||

        "SUNYOUNG ERP";




    const options = {


        body:

        payload.data?.body

        ||

        "새로운 알림이 있습니다.",



        icon:

        "https://sunyoung-approval-system.onrender.com/static/icon.png",



        badge:

        "https://sunyoung-approval-system.onrender.com/static/icon.png",



        vibrate:[

            200,
            100,
            200

        ],



        data:{


            url:

            "https://sunyoung-approval-system.onrender.com/main"


        }


    };



    self.registration.showNotification(

        title,

        options

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