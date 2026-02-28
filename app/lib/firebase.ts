import { initializeApp, getApps, getApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
    projectId: "reviewerscanner-dev",
    appId: "1:849761691608:web:3abd9723370091079634ad",
    storageBucket: "reviewerscanner-dev.firebasestorage.app",
    apiKey: "AIzaSyC_36RzU-RBmSpJs-xwwxSEBp1PBwFN0fs",
    authDomain: "reviewerscanner-dev.firebaseapp.com",
    messagingSenderId: "849761691608"
};

// Next.js 환경에서 여러 번 초기화되는 것을 방지합니다.
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
const db = getFirestore(app);

export { db };
