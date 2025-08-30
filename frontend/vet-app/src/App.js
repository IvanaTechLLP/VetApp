import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import "./App.css";

import LoginSignupPage from "./components/LoginSignupPage";
import ErrorBoundary from "./components/ErrorBoundary";
import LandingPage from "./components/LandingPage";
import Landing from "./components/Landing";
import TermsAndConditions from "./components/TermsAndConditions";
import Payments from "./components/Payments";
import Doctor from "./components/DoctorDashboard";
import DoctorRecords from "./components/DoctorRecords"

{/*
  import Upload from "./components/Upload"




  function FileUploadPage({ profile, selectedPetId }) {
    return (
      
      <div className="app-container">
        <div className="left-panel">
          <ImageProcessingForm profile={profile} selectedPetId={selectedPetId}/>
        </div>
      </div>
    );
  }
      function FileUploadPage({ profile, selectedPetId }) {
    return (
      
      <div className="app-container">
        <div className="left-panel">
          <Upload profile={profile} selectedPetId={selectedPetId}/>
        </div>
      </div>
    );
  }
  */}
  // public key from your generated keys








function App() {
  const [profile, setProfile] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedPetId, setSelectedPetId] = useState("");
  

  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;




  useEffect(() => {
  console.log("React App id:",clientId)
    const storedUser = localStorage.getItem("user");
    if (storedUser && storedUser !== "undefined") {
      console.log("User found in localStorage:", storedUser); // Add this line
      setProfile(JSON.parse(storedUser));
      setIsAuthenticated(true);
    } else {

      console.log("No user in localStorage"); // Add this line
    }
  }, [setProfile, setIsAuthenticated]);

  const logOut = () => {
    console.log("Logging out...");
    localStorage.removeItem("user");
    setProfile(null);
    setIsAuthenticated(false);
    window.location.href = "/"; // Redirect to landing page after logout
  };

  console.log(isAuthenticated);
  return (
    <GoogleOAuthProvider clientId={clientId}>
      <ErrorBoundary>
        <Router>
          <Routes>
            <Route
              path="/"
              element={
                <LandingPage/>
              }
              
            />
             <Route
              path="/landing"
              element={
                <Landing/>
              }
              
            />
            <Route
              path="/termsandconditions"
              element={
                <TermsAndConditions />
              }
            />
          
          
           {/*}
            <Route
              path="/login"
              element={
                <LoginSignupPage
                  setProfile={setProfile}
                  setIsAuthenticated={setIsAuthenticated}
                />
              }
            />
            <Route
              path="/loginn"
              element={
                <LoginPage
                  setProfile={setProfile}
                  setIsAuthenticated={setIsAuthenticated}
                />
              }
            />

            */}
            <Route
              path="/login"
              element={
                <LoginSignupPage
                  setProfile={setProfile}
                  setIsAuthenticated={setIsAuthenticated}
                />
              }
            />
             

         
            {/*
           
              <Route
              path="/upload"
              element={
                isAuthenticated ? (
                  <FileUploadPage profile={profile} logOut={logOut} selectedPetId={selectedPetId} />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
             <Route
              path="/home"
              element={
                isAuthenticated ? (
                  <Home
                    profile={profile}
                    logOut={logOut}
                    reports={reports}
                    setReports={setReports}
                    selectedPetId={selectedPetId}
                  />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
            */}
          
            
        
           
            
            

            {/*
            <Route
              path="/calendar"
              element={
                isAuthenticated ? (
                  <Calendar 
                    logOut = {logOut}
                    profile = {profile}
                  />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
            <Route
              path="/qr_dashboard/:user_id"
              element={
                <QR_DashboardPage
                  reports={reports}
                  setReports={setReports}
                  profile={profile}
                  setProfile={setProfile}
                />
              }
            />
            <Route
              path="/chat"
              element={
                isAuthenticated ? (
                  <ChatWindow profile={profile} logOut={logOut} selectedPetId={selectedPetId} />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
            <Route
              path="/doctor"
              element={
                isAuthenticated ? (
                  <Doctor profile={profile} logOut={logOut} />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
            {/* QR Scanner route - Only accessible by doctors 
              <Route
              path="/qrscanner"
              element={
                isAuthenticated ? (
                  <QrScanner /> // Render the QR scanner if the user is a doctor
                ) : (
                  <Navigate to="/" /> // Redirect non-doctors to the home page
                )
              }
            />
              <Route
              path="/profile"
              element={
                isAuthenticated ? (
                  <UserPage profile={profile} logOut={logOut} selectedPetId={selectedPetId} setSelectedPetId={setSelectedPetId}/>
                ) : (
                  <Navigate to="/" />
                )
              }
            />
            <Route
              path="/timeline"
              element={
                isAuthenticated ? (
                  <Timeline profile={profile} logOut={logOut} selectedPetId={selectedPetId} />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
            */}
             <Route
              path="/doctor"
              element={
                isAuthenticated ? (
                  <Doctor profile={profile} logOut={logOut} />
                ) : (
                  <Navigate to="/" />
                )
              }
            />

              <Route
              path="/doctor-records"
              element={
                isAuthenticated ? (
                  <DoctorRecords profile={profile} logOut={logOut} />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
          
         


            

          </Routes>
        </Router>
      </ErrorBoundary>
    </GoogleOAuthProvider>
  );
}

export default App;
