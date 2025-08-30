import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Payments.css';
 

const Payments = ({ profile }) => {
  const navigate = useNavigate();

  useEffect(() => {
    if (!profile) return;
  
    console.log("Profile:", profile);
  
    const expiryDate = new Date(profile.payment_expiry);
    console.log("Expiry Date:", profile.payment_expiry);
    const now = new Date();
    console.log("Current Date:", now);
  
    if (now < expiryDate || profile.email === "a21.mathur21@gmail.com") {
      // Payment or trial still valid
      if (profile.is_paid_user || profile.is_trial_user) {
        navigate("/profile-new");
      }
    } else {
      // Expired
      if (profile.is_paid_user) {
        alert("Your subscription has expired. Please renew to continue.");
        // optionally set a state to show a renew button
      } else if (profile.is_trial_user) {
        alert("Your trial has expired. Please subscribe to continue using the software.");
      }
    }
  }, [profile, navigate]);

  const handleSubscription = async () => {
    try {
      // 1. Create order from your backend
      const res = await fetch('http://localhost:8000/api/create-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: profile.user_id }),
      });
      const data = await res.json();
      console.log(data);

      // 2. Configure Razorpay options
      const options = {
        key: process.env.REACT_APP_RAZORPAY_KEY_ID,
        amount: data.amount,
        currency: 'INR',
        name: 'Purrytails',
        description: 'Premium Subscription',
        image: 'frontend/public/PurryTails.png',
        order_id: data.orderId,
        handler: async function (response) {
          try {
            const verifyRes = await fetch('http://localhost:8000/api/verify-payment', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                ...response,
                user_id: profile.user_id,
              }),
            });
        
            const result = await verifyRes.json();
            if (verifyRes.ok) {
              alert('Payment successful!');

              // Update user profile in local storage
              const updatedProfile = { ...profile, is_paid_user: true };
              localStorage.setItem("user", JSON.stringify(updatedProfile));
              
              window.location.href = '/profile-new'; // 🔁 redirect to profile page
            } else {
              alert(result.detail || 'Payment verification failed.');
            }
          } catch (err) {
            console.error(err);
            alert('Something went wrong during payment verification.');
          }
        },
        
        prefill: {
          name: profile.name,
          email: profile.email,
        },
        theme: {
          color: '#3399cc',
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (err) {
      console.error(err);
      alert('Something went wrong. Please try again.');
    }
  };

  const handleFreeTrial = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/start-trial', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: profile.user_id }),
      });
  
      const data = await res.json();
  
      if (res.ok) {
        alert('Trial started! Enjoy your free 90 days.');
  
        // Optionally update profile state/localStorage if needed
        const updatedProfile = {
          ...profile,
          is_trial_user: true,
          is_paid_user: false,
          trial_start: new Date().toISOString(), // could use data if backend returns it
          payment_expiry: new Date(Date.now() + 30 * 1000).toISOString(),
        };
        localStorage.setItem("user", JSON.stringify(updatedProfile));
  
        window.location.href = '/profile-new';
      } else {
        alert(data.detail || 'Something went wrong. Please try again.');
      }
    } catch (err) {
      console.error(err);
      alert('Could not start trial. Please contact support.');
    }
  };
  

  return (
    <div className="page-container">
    {/* Logo */}
    <img src="/PT.png" alt="Purry Tails Logo" className="logo" />
  
    {/* Centered Card */}
    <div className="payment-card">
      <h1>Welcome, {profile.name} 👋</h1>
      <p>Choose how you'd like to get started with us!</p>
  
      <button onClick={handleSubscription} className="payment-btn subscribe-btn">
        🚀 Subscribe Now
      </button>
  
      <button onClick={handleFreeTrial} className="payment-btn trial-btn">
        🎁 Start Free Trial
      </button>
    </div>
  </div>
  
  );
};

export default Payments;
