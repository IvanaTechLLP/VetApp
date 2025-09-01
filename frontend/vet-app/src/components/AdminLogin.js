// src/pages/AdminLoginPage.js
import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import axios from "axios";
import "./LoginSignupPage.css";

const AdminLoginPage = ({ setProfile, setIsAuthenticated }) => {
  const [user, setUser] = useState(null);
  const userType = "admin";
  const navigate = useNavigate();

  const login = useGoogleLogin({
    onSuccess: (codeResponse) => {
      setUser(codeResponse);
      localStorage.setItem("access_token", codeResponse.access_token);
    },
    onError: (error) => console.log("Login Failed:", error),
    scope: "openid profile email",
  });

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

          const cached_user_data = res.data;

          axios
            .post("/api/admin_login", {
              email: res.data.email,
              name: res.data.name,
            })
            .then((response) => {
              const payload = response?.data;
              if (!payload?.status) {
                console.error("Admin Login API failed:", payload);
                throw new Error(payload?.message || "Admin login failed");
              }

              const adminId = payload?.data?.admin_id;
              if (!adminId) {
                console.error("admin_id missing in response:", payload);
                throw new Error("admin_id missing");
              }

              setProfile((prevProfile) => ({
                ...prevProfile,
                user_id: adminId, // map admin_id → user_id
                user_type: userType,
              }));

              cached_user_data.user_id = adminId;
              cached_user_data.user_type = userType;
              localStorage.setItem("user", JSON.stringify(cached_user_data));
              console.log("jwt", payload.data.token);
              localStorage.setItem("jwt", payload.data.token);

              navigate("/admin"); // redirect to admin dashboard
            })
            .catch((err) => {
              console.log("Backend Error:", err);
              alert(err?.response?.data?.detail?.message || "Admin login failed");
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
          <h2>Admin Login</h2>
          <p>Sign in with your admin Google account</p>

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

export default AdminLoginPage;
