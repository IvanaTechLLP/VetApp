import React from "react";
import "./footer.css";

const Footer = () => {
  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      const offset = 150;
      const elementPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({
        top: elementPosition,
        behavior: "smooth",
      });
    }
  };

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <footer className="footer">
      <div className="footer-left">
        <a href="#" className="footer-logo-link">
  <img src="/PT.png" alt="Purry Tails Logo" className="footer-logo" />
</a>

      </div>

      <div className="footer-center">
        <nav className="footer-links">
          <a onClick={() => scrollToSection("aboutus")}>About Us</a>
          <a onClick={() => scrollToSection("perks")}>Features</a>
          <a onClick={() => scrollToSection("journey")}>User Flow</a>
        </nav>
      </div>

      <div className="footer-right">
        <h4>Contact us</h4>
        <h5>mahir@purrytails.in</h5>

        {/* Company Info */}
  <div style={{ marginTop: "10px", fontSize: "14px", fontFamily: "Poppins, sans-serif", color: "#333" }}>
    <strong>IVANA TECH LLP</strong><br />
    303, SIDHHI DEEP CHS LTD, Vile Parle East<br />
    Mumbai, Maharashtra 400057, India
  </div>
        <div className="footer-social-icons" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
  
  {/* Instagram */}
  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
    <a href="https://www.instagram.com/purry.tails?igsh=MWZnOW16NjY1anZidA==" target="_blank" rel="noopener noreferrer">
      <img src="insta1.png" alt="Instagram" style={{ width: "40px", height: "40px" }} />
    </a>
    <span style={{ fontSize: "16px", fontFamily: "Poppins, sans-serif", color: "#333" }}>
      @purry.tails
    </span>
  </div>

  {/* LinkedIn */}
  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
    <a href="https://www.linkedin.com/company/purry-tails" target="_blank" rel="noopener noreferrer">
      <img src="link.png" alt="LinkedIn" style={{ width: "30px", height: "30px" }} />
    </a>
    <span style={{ fontSize: "16px", fontFamily: "Poppins, sans-serif", color: "#333" }}>
      @purry-tails
    </span>
  </div>

  {/* X (formerly Twitter) */}
  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
    <a href="https://x.com/purrytails?s=21" target="_blank" rel="noopener noreferrer">
      <img src="x.png" alt="X" style={{ width: "20px", height: "20px" }} />
    </a>
    <span style={{ fontSize: "16px", fontFamily: "Poppins, sans-serif", color: "#333" }}>
      @PurryTails
    </span>
  </div>

</div>


      </div>

      <div className="footer-bottom">
        <p>
          &copy; {new Date().getFullYear()} Purry Tails. All rights reserved.
          <span
          className="text-blue-500 cursor-pointer hover:underline"
          onClick={() => (window.location.href = "/termsandconditions")}
        >
          Terms and Conditions
        </span>
        </p>
      </div>
    </footer>
  );
};

export default Footer;
