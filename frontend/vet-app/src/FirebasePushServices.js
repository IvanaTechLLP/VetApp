// /src/services/firebasePushService.js
import { getMessaging, getToken } from "firebase/messaging";
import { initializeApp } from "firebase/app";

// Your Firebase config (from the screenshot earlier)
const firebaseConfig = {
  apiKey: "AIzaSyAZ3k8LDCb5fwkEhB7qlOqBbvXkYR22qE",
  authDomain: "vet-app-25c6a.firebaseapp.com",
  projectId: "vet-app-25c6a",
  storageBucket: "vet-app-25c6a.appspot.com",
  messagingSenderId: "784887310237",
  appId: "1:784887310237:web:e5dc10da25f69290be3174",
  measurementId: "G-SM9SMJLX5D"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

export const requestPushPermission = async (userId) => {
  try {
    const token = await getToken(messaging, { vapidKey: "BLczqB44i3rgoBSM-gE3hgI_AxmBsOJHdwsJm0g7UF65TOBQ_CA74SET6W_RKWgNROOC6ZN8HOjyUhfsYiwpL9A" });
    if (token) {
      console.log("Push Token:", token);
      // Send the token to your backend along with the userId
      await fetch("/api/save_push_token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, push_token: token })
      });
    }
  } catch (error) {
    console.error("Push token error:", error);
  }
};
