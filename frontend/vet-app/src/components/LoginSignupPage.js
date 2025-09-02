import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import axios from "axios";
import "./LoginSignupPage.css";

const LoginSignupPage = ({ setProfile, setIsAuthenticated }) => {
  const [user, setUser] = useState(null);
  const userType = "doctor"; // Always doctor
  const navigate = useNavigate();

  const login = useGoogleLogin({
    onSuccess: (codeResponse) => {
      setUser(codeResponse);
      localStorage.setItem("access_token", codeResponse.access_token);
    },
    onError: (error) => console.log("Login Failed:", error),
    scope: "openid profile email",
  });
  const API_BASE_URL = process.env.REACT_APP_API_URL;

  useEffect(() => {
    if (user) {
      axios
        .get(
          `https://www.googleapis.com/oauth2/v1/userinfo?access_token=${user.access_token}`,
          {
            headers: {
              Authorization: `Bearer ${user.access_token}`,
              Accept: "application/json",
            },
          }
        )
        .then((res) => {
          setProfile(res.data);
          setIsAuthenticated(true);
          

          // inside the .then((res) => { ... }) after Google userinfo
const cached_user_data = res.data;

axios
  .post(`${API_BASE_URL}/api/doctor_login`, {
    email: res.data.email,
    name: res.data.name,
  })
  .then((response) => {
    const payload = response?.data;
    if (!payload?.status) {
      console.error("Login API failed:", payload);
      throw new Error(payload?.message || "Login failed");
    }
    const doctorId = payload?.data?.doctor_id;
    if (!doctorId) {
      console.error("doctor_id missing in response:", payload);
      throw new Error("doctor_id missing");
    }

    setProfile((prevProfile) => ({
      ...prevProfile,
      user_id: doctorId,      // map doctor_id → user_id for the rest of the app
      user_type: userType,
    }));

    cached_user_data.user_id = doctorId;
    cached_user_data.user_type = userType;
    localStorage.setItem("user", JSON.stringify(cached_user_data));
    console.log("jwt", payload.access_token);
localStorage.setItem("jwt", payload.access_token);
  // ✅ Save JWT here


    navigate("/doctor");
  })
  .catch((err) => {
    console.log("Backend Error:", err);
    alert(err?.response?.data?.detail?.message || "Login failed");
  });

        })
        .catch((err) => console.log("Google Profile Fetch Error:", err));
    }
  }, [user, navigate, setProfile, setIsAuthenticated]);

  return (
    <div className="login-page">
      <Link to="/">
        <img src="PT.png" alt="Purry Tails Logo" className="logo" />
      </Link>

      <div className="login-container">
        <div className="login-form">

          <div className="social-cause-info">
            <h2>Our Social Cause</h2>
            <p>
              Together, we can make a difference. Your support helps us bring
              quality healthcare to those in need and create a lasting impact on
              lives. Join us in our mission to spread hope and heal.
            </p>
            <Link to="/">Learn More</Link>
          </div>

          <p>Join us in spreading hope.</p>

          <button className="google-signin-button" onClick={login}>
            <img src="/google-logo.png" alt="Google Logo" />
            Sign in with Google
          </button>
        </div>
      </div>

      <div className="illustration">
        <img src="login.png" alt="Illustration" />
      </div>
    </div>
  );
};

export default LoginSignupPage;
