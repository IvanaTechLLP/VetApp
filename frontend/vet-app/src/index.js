import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

reportWebVitals();

// ----------------- PUSH NOTIFICATION SETUP -----------------
if ('serviceWorker' in navigator && 'PushManager' in window) {
  navigator.serviceWorker.register('/service-worker.js').then(function (reg) {
    console.log('Service Worker registered ✅', reg);

    // Ask for notification permission
    Notification.requestPermission().then(function (permission) {
      if (permission === 'granted') {
        console.log('Notification permission granted.');
        subscribeUser(reg);
      }
    });
  });
}

function subscribeUser(reg) {
  reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array("MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAENDg2ezceVN-A2KMGua6eGXFvG46z53r5wnfhl1QGQAm3bXzg1IZEzRoUMNqH_qtDLUzA3meFL_QkBpkHqOfiYQ")

  })
  .then(function (subscription) {
    console.log('User subscribed:', JSON.stringify(subscription));
    // TODO: Send subscription to your server & save in DB
  })
  .catch(function (err) {
    console.error('Failed to subscribe user:', err);
  });
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map(char => char.charCodeAt(0)));
}
