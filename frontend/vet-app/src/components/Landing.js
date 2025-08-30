import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Landing.css";
import Footer from "./footer";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import { FiFileText, FiLayout, FiBell, FiShare2 } from "react-icons/fi";




const reviews = [
  {
    author: "Dhruv G",
    text: "I love this platform! It has transformed how I manage my dogs' health records. I can share their information with vets quickly, and I no longer worry about losing important documents. Purry Tail makes it simple to keep everything organized. I feel more confident knowing that the health information is secure and accessible whenever I need it."
  },
  {
    author: "Himani T",
    text: "As a busy pet parent, I always struggled to keep track of my cat's health records, vaccinations, and vet visits. Purry Tails has been a game-changer for me! I can easily access and update all my cat's information in one place. I highly recommend it to all pet parents!"
  },
  {
    author: "Kritika B",
    text: "Purry Tails is a must-have for any pet parent! I appreciate being able to track my dogs' health histories and medications easily. It's comforting to know I can keep everything related to my pets' health in one secure place. Thank you for creating such a fantastic resource!"
  }
];


const Landing = () => {
  const [activeService, setActiveService] = useState(null);
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const [isPopupVisible, setPopupVisible] = useState(false);
  const [popupContent, setPopupContent] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');


  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      const offset = 120; 
      const elementPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({
        top: elementPosition,
        behavior: "smooth"
      });
    }
    setIsOpen(false)
  }
  const scrollToSectionMobile = (e, id) => {
    e.preventDefault(); // Prevent default anchor link behavior
    const element = document.getElementById(id);
  
    if (element) {
      // Define your offset value based on the height of fixed elements like headers or nav bars
      const offset = 70; // You can adjust this value based on your header's height
  
      // Use scrollIntoView with smooth scrolling
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
  
      // For Android or other devices, handle the scroll offset manually (if needed)
      // Android usually handles this well with just scrollIntoView, but you can manually adjust if required
      setTimeout(() => {
        window.scrollBy(0, -offset);
      }, 500); // Add a small delay to ensure smooth scrolling is applied
    }
  
    setMenuOpen(false); // Close the menu after clicking on a link
  };
  
  
  const [isOpen, setIsOpen] = useState(false);

  const handleLoginClick = () => {
    navigate("/login");
  };


 
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0);

  const nextReview = () => {
    setCurrentReviewIndex((prevIndex) => (prevIndex + 1) % reviews.length);
  };

  const prevReview = () => {
    setCurrentReviewIndex((prevIndex) => (prevIndex - 1 + reviews.length) % reviews.length);
  };
  const openPopup = (content, video) => {
    setPopupContent(content);
    setVideoUrl(video);
    setPopupVisible(true);
  };

  const closePopup = () => {
    setPopupVisible(false);
    setPopupContent(null);
    setVideoUrl('');
  };
  const toggleMobileMenu = () => {
    setMenuOpen(prev => !prev);
  };
  const [form, setForm] = useState({
    name: "",
    practice: "",
    email: "",
    phone: "",
    message: ""
  });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null); // 'success' | 'error'
  const [statusMsg, setStatusMsg] = useState("");
  
  
  function validate() {
    const e = {};
    if (!form.name.trim()) e.name = "Name is required";
    if (!form.email.trim()) e.email = "Email is required";
    else if (!/^\S+@\S+\.\S+$/.test(form.email)) e.email = "Invalid email";
    if (!form.phone.trim()) e.phone = "Phone is required";
    if (!form.message.trim()) e.message = "Message is required";
    return e;
  }

  function handleChange(e) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setErrors(prev => ({ ...prev, [e.target.name]: null }));
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    const e = validate();
    if (Object.keys(e).length) {
      setErrors(e);
      return;
    }

    setBusy(true);
    setStatus(null);

    try {
      // TODO: Integrate reCAPTCHA here if required and send token with payload
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || "Failed to send. Try again.");
      }

      setStatus("success");
      setStatusMsg("Thanks — we got your message. We'll be in touch soon.");
      setForm({ name: "", practice: "", email: "", phone: "", message: "" });
    } catch (err) {
      setStatus("error");
      setStatusMsg(err.message || "Something went wrong. Please try again later.");
    } finally {
      setBusy(false);
    }
  }



  return (
    <div className="landing-container">
        <nav className="landingNavNew">
    
            <div className="navLeft">
              <a href="#">
                <img src="/PT.png" alt="Purry Tails Logo" />
              </a>
            </div>


            <ul className="navCenter">
              <li><a onClick={() => scrollToSection("aboutus")}>About Us</a></li>
              <li><a onClick={() => scrollToSection("perks")}>Features</a></li>
              <li><a onClick={() => scrollToSection("journey")}>User Flow</a></li>
              <li><a onClick={() => scrollToSection("reviews")}>Testimonials</a></li>
              <li><a onClick={() => scrollToSection("about")}>Our Team</a></li>
            </ul>


            <div className="navRight">
              <button onClick={handleLoginClick} className="btnSecondary">Login</button>
              <button className="btnPrimary">Schedule a Demo</button>
            </div>
            
        </nav>

          <div class="mobileNav">
            <div class="logo">
              <a href="#"></a>
              <img src="PT.png" alt="Logo" />
            </div>
            <div class="navActions">
              <button class="btnScheduleDemo">Schedule Demo</button>
              <button className="hamburger" onClick={toggleMobileMenu}>
            {menuOpen ? "×" : "☰"}
          </button>
            </div>

            <div className={`mobileMenu ${menuOpen ? "open" : ""}`}>
        <a href="#ourmission">About Us</a>
        <a href="#perks">Features</a>
        <a href="#journey">User Flow</a>
        <a href="#reviews">Testimonials</a>
        <a href="#about">Our Team</a>
        <a href="/login">Login</a>
      </div>
          </div>

          


     
  


      

      
      <button className="contact-us-button" onClick={handleLoginClick}>
        Login
      </button>
      
      
    
<section className="hero">
  <div className="hero-inner">
    {/* Left column: text + CTA */}
    <div className="hero-left">
      <h1 className="hero-title">
    Veterinary software solutions that keeps Pet Parents Connected to your Clinic
      </h1>
      <p className="hero-subtitle">
    Purry Tails helps clinics share updates, send reminders, and keep pet parents at ease with AI tools.
      </p>
      <button className="hero-cta" onClick={() => (window.location.href = "/schedule")}>
        Schedule a Demo
      </button>
    </div>

    {/* Right column: image */}
    <div className="hero-right">
      <img src="/HeroImage1.png" alt="Purry Tails - Pet Health" className="hero-image" />
    </div>
  </div>
</section>


       


      {/*}
      <div className="landing-container1">
    
        <div className="info-boxes-section">
        <div className="info-box">
          <h2 className="info-number">999+</h2>
          <p className="info-text">Documents Stored</p>
        </div>
        <div className="info-box">
          <h2 className="info-number">99+</h2>
          <p className="info-text">Happy Pets</p>
        </div>
        <div className="info-box">
          <h2 className="info-number">9+</h2>
          <p className="info-text">Partnered Vets</p>
        </div>
        <div className="info-box">
          <h2 className="info-number">99+</h2>
          <p className="info-text">Smart Health Cards Provided</p>
        </div>
      </div>
      </div>
                <div className="landing-section">
  <div className="landing-item">
    <img src="/c1.png" className="landing-image" alt="Empowering Your Pet's Health" />
    <div className="landing-content">
      <h5>Empowering Your Pet's Health</h5>
      <p>All your pet's medical and vaccination records in one secure place.</p>
    </div>
  </div>
</div>
          */}

    <section className="features-section">
  <div className="features-header">
       <span className="why-badge">India’s First</span>
    <h2 className="features-title">
      Smarter Veterinary Care, <br /> Happier Pet Parents
    </h2>
    <p className="features-subtitle">
      Powerful features designed for vets, clinics, and pet parents — all in one seamless platform.
    </p>
  </div>

  <div className="features-body">
    {/* Left: 30% Image */}
    <div className="features-image">
      <img src="/images/vet-dashboard.png" alt="Vet App Dashboard" />
    </div>

    {/* Right: 70% Grid */}
    <div className="features-content">
      <div className="features-grid">
        <div className="feature-card">
          <span className="feature-icon"><FiFileText /></span>
          <h3>Smart AI Uploads</h3>
          <p>Upload reports & prescriptions in seconds. AI extracts medical info & creates a structured pet health timeline.</p>
        </div>

        <div className="feature-card">
          <span className="feature-icon"><FiLayout /></span>
          <h3>White-Labeled Portal</h3>
          <p>Your clinic’s own branded portal. Pet parents can access records, prescriptions & vaccination schedules anytime.</p>
        </div>

        <div className="feature-card">
          <span className="feature-icon"><FiBell /></span>
          <h3>Smart Reminders</h3>
          <p>Automated reminders for vaccines, deworming & checkups. WhatsApp + push notifications ensure zero missed appointments.</p>
        </div>

        <div className="feature-card">
          <span className="feature-icon"><FiShare2 /></span>
          <h3>Easy Sharing</h3>
          <p>Share prescriptions & updates instantly. Pet parents can send back progress securely via the portal.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section className="why-section">
  <div className="why-header">
    <span className="why-badge">The Purry Tails Difference</span>
    <h2 className="why-title">Why Choose Purry Tails?</h2>
    <p className="why-subtitle">
      AI-driven aftercare that reduces admin, strengthens client trust, and keeps pets healthier.
    </p>
  </div>

  <div className="why-grid">
    {/* Left: primary card (tall, spans 2 rows) */}
    <div className="why-card card-primary">
      <h3>Less Admin, More Care</h3>
      <p>
        Automate extraction, filing and history-building so your team spends less time on paperwork and more time with patients.
      </p>
      <img
        src="/images/health-timeline.png"
        alt="Health Timeline"
        className="card-shot"
      />
    </div>

    {/* Right top: reminders card (with product screenshot) */}
    <div className="why-card">
       <h3>Stronger Clinic Brand</h3>
      <p>
        A white-labeled parent portal builds trust and loyalty — your clinic’s
        name stays front-and-center with every interaction.
      </p>
    </div>

    {/* Right top: communication card (still with icon or illustration) */}
    <div className="why-card">
      <h3>Smoother Communication</h3>
      <p>
        One-tap sharing and a single conversation thread replace confusing calls,
        emails and scattered WhatsApp messages.
      </p>
    </div>

    {/* Right bottom: portal card with screenshot */}
    <div className="why-card card-wide">

        <h3>Fewer Missed Follow-ups</h3>
      <p>
        Smart reminders (WhatsApp & push) mean more on-time vaccines, checkups
        and medication adherence.
      </p>
      <img
        src="/images/parent-portal.png"
        alt="Parent Portal"
        className="card-shot"
      />
    </div>
  </div>
</section>

   <div className="container">
<section className="adapt-section">
       <span className="why-badge">Easy Adaptation</span>
  <h2 className="adapt-title">Get Started with Purry Tails in Minutes</h2>
  <p className="adapt-subtitle">
    No steep learning curve, no disruption — just a smooth add-on that makes your clinic smarter, faster, and more connected.
  </p>

  <div className="adapt-row">
    <div className="adapt-item">
      <div className="adapt-icon">📄</div>
      <div>
        <h3>Designed for Simplicity</h3>
        <p>
          A clean, two-page interface your staff can understand instantly. No training, no manuals — just plug and play.
        </p>
      </div>
    </div>

    <div className="adapt-item">
      <div className="adapt-icon">💬</div>
      <div>
        <h3>WhatsApp Made Easy</h3>
        <p>
          We set up your clinic’s WhatsApp number so you can send reminders, updates, and reports directly — where your clients already are.
        </p>
      </div>
    </div>
  </div>

  <div className="adapt-row">
    <div className="adapt-item">
      <div className="adapt-icon">🏥</div>
      <div>
        <h3>Your Brand, Your Way</h3>
        <p>
          From your logo to your clinic’s tone, Purry Tails blends seamlessly into your brand so it feels like your own software, not ours.
        </p>
      </div>
    </div>

    <div className="adapt-item">
      <div className="adapt-icon">⚡</div>
      <div>
        <h3>Lightning-Fast Onboarding</h3>
        <p>
          Forget long set-ups — we configure everything in hours, not weeks, so your team is up and running right away.
        </p>
      </div>
    </div>
  </div>

  <div className="adapt-row">
    <div className="adapt-item">
      <div className="adapt-icon">📊</div>
      <div>
        <h3>Effortless Add-On, No Disruption</h3>
        <p>
           Enhances your clinic’s daily flow without replacing your current tools — it’s designed to work alongside them.
        </p>
      </div>
    </div>

    <div className="adapt-item">
      <div className="adapt-icon">🛠️</div>
      <div>
        <h3>Dedicated Support</h3>
        <p>
          Whether it’s a quick question or ongoing help, our team is always just a call or click away — so you never feel stuck.
        </p>
      </div>
    </div>
  </div>

</section>
</div>




  
<section className="contact-section" aria-labelledby="contact-heading">
  <h2 id="contact-heading" className="contact-title">Let's Connect — We're Here to Help</h2>
      <p className="contact-sub">Tell us about your clinic and how we can help — we'll reply within one business day.</p>

  <div className="contact-wrapper">
  <div className="contact-left">
      
      <form className="contact-form" onSubmit={handleSubmit} noValidate>
        <div className="row two">
          <label className="field">
            <span className="label">First name</span>
            <input name="name" value={form.name} onChange={handleChange} placeholder="Name*" />
            {errors.name && <div className="err">{errors.name}</div>}
          </label>

          <label className="field">
            <span className="label">Practice name</span>
            <input name="practice" value={form.practice} onChange={handleChange} placeholder="Practice name" />
            {errors.practice && <div className="err">{errors.practice}</div>}
          </label>
        </div>

        <div className="row two">
          <label className="field">
            <span className="label">Email</span>
            <input name="email" value={form.email} onChange={handleChange} placeholder="Email*" />
            {errors.email && <div className="err">{errors.email}</div>}
          </label>

          <label className="field">
            <span className="label">Phone</span>
            <input name="phone" value={form.phone} onChange={handleChange} placeholder="Phone*" />
            {errors.phone && <div className="err">{errors.phone}</div>}
          </label>
        </div>

        <label className="field full">
          <span className="label">Message</span>
          <textarea
            name="message"
            value={form.message}
            onChange={handleChange}
            placeholder="Tell us about your practice and any problems you are facing"
            rows="5"
          />
          {errors.message && <div className="err">{errors.message}</div>}
        </label>

        {/* If using reCAPTCHA, render widget or invisible token here */}
        <div className="form-actions">
          <button className="btn primary" type="submit" disabled={busy}>
            {busy ? "Sending..." : "Request a Demo"}
          </button>
          <div className="small-note">We respect your privacy — we won’t share your data.</div>
        </div>

        {status === "success" && <div className="form-status success">{statusMsg}</div>}
        {status === "error" && <div className="form-status error">{statusMsg}</div>}
      </form>

      </div>
      <div className="contact-right">
      <img 
        src="/images/doctor-smile.jpg" 
        alt="Veterinarian smiling" 
        className="contact-image"
      />
    </div>
    </div>
    </section>


<div className="landing-container1">
<div id="journey" className="journey-section">
  <h1>Welcome to Your Companion's Health Journey</h1>

  {/* Always visible Journey Steps */}
  <div className="journey-step left">
    <div className="image-container">
      <img className="left-image-landing" src="login-left.jpg" alt="Step 1" />
    </div>
    <div className="text-container">
      <h2>1 SIGN IN</h2>
      <ul className="journey-custom-list">
  <li className="journey-custom-item">- Sign in with Google</li>
  <li className="journey-custom-item">- Access from any device</li>
  <li className="journey-custom-item">- Quick, easy setup</li>
  </ul>

  <h4>"Your Gateway to Smarter Healthcare!"</h4>
    </div>
  </div>

  <div className="journey-step right">
    <div className="image-container">
      <img className="right-image-landing" src="right-details.png" alt="Step 2" />
    </div>
    <div className="text-container">
      <h2>2 ENTER YOUR PROFILE DETAILS</h2>
      
      <ul className="journey-custom-list">
     
  <li className="journey-custom-item">- Add pet vitals (age, weight, etc.)</li>
  <li className="journey-custom-item">- Upload a cute pet photo</li>
  <li className="journey-custom-item">- Fill Out Pet parent details</li>
  
  </ul>
      <h4>"Where Your Story Begins!"</h4>
    </div>
  </div>

  <div className="journey-step left">
    <div className="image-container">
      <img className="left-image-landing" src="image-upload.jpg" alt="Step 3" />
    </div>
    <div className="text-container">
      <h2>3 UPLOAD REPORTS</h2>
      
      <ul className="journey-custom-list">
      <li className="journey-custom-item">- Save time with easy uploads</li>
  <li className="journey-custom-item">- Upload reports in any format</li>
  <li className="journey-custom-item">- Let AI extract key medical details</li>

  </ul>
      <h4>"Effortless Upload, Smarter Insights!"</h4>
    </div>
  </div>

  <div className="journey-step right">
    <div className="image-container">
      <img className="right-image-landing" src="right-dashboard.png" alt="Step 4" />
    </div>
    <div className="text-container">
      <h2>4 DASHBOARD</h2>
      
      <ul className="journey-custom-list">
  <li className="journey-custom-item">- Manage all reports in one place</li>
  <li className="journey-custom-item">- Use AI chatbot for quick access</li>
  <li className="journey-custom-item">- Find documents with simple queries</li>
  </ul>

      <h4>"Stay Informed, Stay Empowered!"</h4>
    
    </div>
  </div>

  <div className="journey-step left">
    <div className="image-container">
      <img className="left-image-landing" src="left-timeline.jpg" alt="Step 5" />
    </div>
    <div className="text-container">
      <h2>5 HEALTH TIMELINE</h2>
      
              <ul className="journey-custom-list">

          <li className="journey-custom-item">- Easy access to timeline summary</li>
          <li className="journey-custom-item">- Download or share with doctors</li>
          <li className="journey-custom-item">- Easily spot trends in your health</li>
        </ul>
    
      <h4>"Your Complete Medical Journey at a Glance!"</h4>
    </div>
  </div>
</div>




<div id="reviews" className="reviews-section">
      <h1>What Our Users Say</h1>
      <div className="reviews-navigation-container">
    <img 
      src="/paw-left.png" 
      alt="Previous Review" 
      onClick={prevReview} 
      className="nav-button"
    />
    <div className="review-box">
      <p className="review-author">{reviews[currentReviewIndex].author}</p>
      <p className="review-text">{reviews[currentReviewIndex].text}</p>
    </div>
    <img 
      src="/paw-right.png" 
      alt="Next Review" 
      onClick={nextReview} 
      className="nav-button"
    />
  </div>
    </div>
      
      

      


    <div id="about" className="about-us-section">
  <h1>Meet Our Founders</h1>
  <div className="founders">
    <div className="founder">
      <div className="circle">
        <img src="/Da.png" alt="Founder 1" className="founder-image" />
      </div>
      <h2>Darsh Thakkar</h2>
      <p>A dedicated pet parent for over 10 years and passionate animal lover. Manages business development and technology integration for Purry Tails.</p>
    </div>
    <div className="founder">
      <div className="circle">
        <img src="/mair1.png" alt="Founder 2" className="founder-image" />
      </div>
      <h2>Mahir Madhani</h2>
      <p>Compassionate advocate for pets and their well-being. Manages finance and marketing, ensuring Purry Tails' financial health and market presence.</p>
    </div>
    <div className="founder">
      <div className="circle">
        <img src="/abhay1.png" alt="Founder 3" className="founder-image" />
      </div>
      <h2>Abhay Mathur</h2>
      <p>A devoted pet lover. Drives technological innovation, ensuring Purry Tails leverages the latest advancements for a cutting-edge platform.</p>
    </div>
  </div>


      </div>
      </div>
      <Footer />
      

      
    </div>
  );
};

export default Landing;