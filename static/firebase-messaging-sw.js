importScripts(
"https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"
);

importScripts(
"https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js"
);



firebase.initializeApp({

apiKey: "AIzaSyAMMkwzgYkjXT6iKP0WvNT6HSUMAy9Imw0",

authDomain: "sunyoung-erp-push.firebaseapp.com",

projectId: "sunyoung-erp-push",

storageBucket: "sunyoung-erp-push.firebasestorage.app",

messagingSenderId: "1055876715145",

appId: "1:1055876715145:web:f073ec7cef610fd830ac58"

});



const messaging = firebase.messaging();



messaging.onBackgroundMessage(
function(payload) {


console.log(
"백그라운드 메시지:",
payload
);


const notificationTitle =
payload.notification.title;


const notificationOptions = {

body:
payload.notification.body,

icon:
"/static/icon.png"

};


self.registration.showNotification(
notificationTitle,
notificationOptions
);


});