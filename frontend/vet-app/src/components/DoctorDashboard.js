import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./DoctorDashboard.css";
import "react-datepicker/dist/react-datepicker.css";
import { useReactToPrint } from "react-to-print";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const DoctorDashboard = ({ profile }) => {

  const [selectedOption, setSelectedOption] = useState("upload");
  const [reminderValue, setReminderValue] = useState("");
  const [customReminderNumber, setCustomReminderNumber] = useState("");

  const [petName, setPetName] = useState("");
  const [whatsappAccessToken, setWhatsappAccessToken] = useState("");
  const[whatsappNumberId, setWhatsappNumberId] = useState("");


const [petParentNumber, setPetParentNumber] = useState("");



  const [customReminderUnit, setCustomReminderUnit] = useState("days");
    const [weight, setWeight] = useState("");           // Weight in kg
  const [temperature, setTemperature] = useState(""); 
  const [selectedFur, setSelectedFur] = useState("");   // Track selected fur/coat condition
  const [selectedSkin, setSelectedSkin] = useState(""); // Track selected skin condition

  const steps = ["Vitals", "Physical Exam", "Symptoms", "Diagnosis", "Prescription", "Follow-Up"];
  const [step, setStep] = useState(0);
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [otherSymptoms, setOtherSymptoms] = useState("");
  const reportTypeEl = document.getElementById("reportType");
  const reportType = reportTypeEl ? reportTypeEl.value : "Unknown";
    const [medicines, setMedicines] = useState([
    { name: "", dosage: "once a day", duration: "" },
  ]);

  const addMedicine = () => {
    setMedicines([...medicines, { name: "", dosage: "once a day", duration: "" }]);
  };

  const updateMedicine = (index, field, value) => {
    const updated = [...medicines];
    updated[index][field] = value;
    setMedicines(updated);
  };

  const [selectedDiagnosis, setSelectedDiagnosis] = useState([]);
  const [customDiagnosis, setCustomDiagnosis] = useState("");

  const allDiagnoses = [
    "Gastroenteritis",
    "Parvovirus infection",
    "Tick fever (Ehrlichiosis, Babesiosis)",
    "Canine distemper",
    "Kennel cough (Bordetella)",
    "Dermatitis (skin allergy)",
    "Flea infestation",
    "Fungal skin infection (Ringworm)",
    "Otitis externa (ear infection)",
    "Conjunctivitis",
    "Urinary tract infection (UTI)",
    "Bladder stones",
    "Kidney disease",
    "Liver disease (Hepatitis)",
    "Arthritis / Joint pain",
    "Hip dysplasia",
    "Dental disease (Gingivitis, Periodontitis)",
    "Obesity",
    "Diabetes mellitus",
    "Hypothyroidism",
    "Heartworm disease",
    "Respiratory infection (Upper or Lower)",
    "Pneumonia",
    "Pyometra",
    "Pregnancy check",
    "Wound infection / Abscess",
    "Fracture / Sprain",
    "Anemia",
    "Heatstroke",
    "General vaccination / Preventive check-up"
  ];

    const toggleDiagnosis = (diag) => {
    setSelectedDiagnosis((prev) =>
      prev.includes(diag)
        ? prev.filter((d) => d !== diag)
        : [...prev, diag]
    );
  };


  const addCustomDiagnosis = () => {
    if (customDiagnosis && !selectedDiagnosis.includes(customDiagnosis)) {
      setSelectedDiagnosis([...selectedDiagnosis, customDiagnosis]);
      setCustomDiagnosis("");
    }
  };

  // Overlay / update form related state
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [doctorName, setDoctorName] = useState("");
  const [doctorPhone, setDoctorPhone] = useState("");
  const [clinicName, setClinicName] = useState("");
  const [updateMessage, setUpdateMessage] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);

  // prevent repeated checks
  const hasCheckedProfileRef = useRef(false);

  const nextStep = () => setStep((prev) => Math.min(prev + 1, steps.length - 1));
  const prevStep = () => setStep((prev) => Math.max(prev - 1, 0));

  const SYMPTOMS = [
    "Vomiting","Diarrhea","Lethargy","Loss of appetite","Limping",
    "Coughing","Sneezing","Excessive scratching","Hair loss","Seizures",
    "Swelling/Lump","Weight loss","Increased thirst","Increased urination",
    "Eye discharge","Ear scratching/shaking head","Breathing difficulty",
    "Aggression/Behavior change"
  ];

  const [menuOpen, setMenuOpen] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const toggleSymptom = (s) => {
    setSelectedSymptoms((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  };

  // Phone normalizer (same logic as your backend)
  const normalizeIndianPhone = (value) => {
    if (!value) return null;
    const digits = value.replace(/\D/g, "");
    if (digits.length === 12 && digits.startsWith("91")) {
      const n = digits.slice(2);
      return /^[6-9]\d{9}$/.test(n) ? `+91${n}` : null;
    }
    if (digits.length === 11 && digits.startsWith("0")) {
      const n = digits.slice(1);
      return /^[6-9]\d{9}$/.test(n) ? `+91${n}` : null;
    }
    if (digits.length === 10 && /^[6-9]\d{9}$/.test(digits)) {
      return `+91${digits}`;
    }
    return null;
  };


  // Fetch canonical profile from backend once and decide whether to show update overlay
  useEffect(() => {
    if (hasCheckedProfileRef.current) return;
    hasCheckedProfileRef.current = true;

    const checkProfileFromServer = async () => {
      try {
        const email = profile?.email || JSON.parse(localStorage.getItem("user"))?.email;
        if (!email) {
          console.warn("No doctor email available to check profile");
          // if we can't determine identity, show form as conservative fallback
          setShowUpdateForm(true);
          return;
        }

        const res = await axios.get("http://localhost:8000/doctor_profile", { params: { email } });
        const serverProfile = res?.data?.data || {};
        console.log("serverProfile:", serverProfile);

        const phoneIsValid = (p) => {
          if (!p) return false;
          return /^\+91[6-9]\d{9}$/.test(p);
        };

        const needsUpdate = !serverProfile.doctor_name || !phoneIsValid(serverProfile.doctor_phone) || !serverProfile.clinic_name;

        if (needsUpdate) {
          setDoctorName(serverProfile.doctor_name || "");
          setDoctorPhone(serverProfile.doctor_phone || "");
          setClinicName(serverProfile.clinic_name || "");
          setShowUpdateForm(true);
        } else {
          setShowUpdateForm(false);
          // initialize local fields from serverProfile so UI shows latest
          setDoctorName(serverProfile.doctor_name || "");
          setDoctorPhone(serverProfile.doctor_phone || "");
          setClinicName(serverProfile.clinic_name || "");
        }

      } catch (err) {
        console.error("Error checking doctor profile:", err);
        // fallback: show the form so user can fix missing items
        setShowUpdateForm(true);
      }
    };

    checkProfileFromServer();
  }, [profile]);


  const navigate = useNavigate();
  const closeMenu = () => {
    setIsOpen(false);
  };
  const toggleMobileMenu = () => {
    setMenuOpen(prev => !prev);
    console.log("Menu Toggle");
  };

  // UPDATE handler (explicit, non-auto-submitting)
  const handleDoctorUpdate = async () => {
    setUpdateMessage("");
    setIsUpdating(true);

    try {
      const email = profile?.email || JSON.parse(localStorage.getItem("user"))?.email;
      if (!email) {
        setUpdateMessage("Missing email identity. Please login again.");
        setIsUpdating(false);
        return;
      }

      const normalized = doctorPhone ? normalizeIndianPhone(doctorPhone) : null;
      if (doctorPhone && !normalized) {
        setUpdateMessage("Please enter a valid Indian phone number.");
        setIsUpdating(false);
        return;
      }

      const payload = {
        doctor_email: email,
        doctor_name: doctorName?.trim() || null,
        doctor_phone: normalized || null,
        clinic_name: clinicName?.trim() || null,
        whatsapp_access_token: whatsappAccessToken?.trim() || null,
        whatsapp_number_id: whatsappNumberId?.trim() || null,

      };

      console.log("Calling doctor_update with:", payload);

      const res = await axios.post("http://localhost:8000/doctor_update", payload, { headers: { "Content-Type": "application/json" } });

      console.log("doctor_update response:", res.data);
      if (res?.data?.status) {
        setUpdateMessage(res.data.message || "Profile updated");

        // write canonical profile to localStorage so overlay won't reappear
        const updatedProfile = {
          ...JSON.parse(localStorage.getItem("user") || "{}"),
          name: res.data.data.doctor_name || doctorName,
          phone: res.data.data.doctor_phone || normalized,
          clinic_name: res.data.data.clinic_name || clinicName,
        };
        localStorage.setItem("user", JSON.stringify(updatedProfile));
      } else {
        setUpdateMessage(res?.data?.message || "Update failed");
      }

      setShowUpdateForm(false);

    } catch (err) {
      console.error("doctor_update error:", err);
      setUpdateMessage(err.response?.data?.detail?.message || err.message || "Update failed");
    } finally {
      setIsUpdating(false);
    }
  };


const savePrescriptionAndSend = async (e) => {
  e.preventDefault();
  console.log("💾 Save Prescription clicked");

  try {
    // 1️⃣ Get the hidden prescription div
    const element = document.getElementById("prescription");
    if (!element) {
      console.error("❌ Prescription element not found!");
      return;
    }
    console.log("✅ Prescription element found");

    // 2️⃣ Convert HTML to canvas
    const canvas = await html2canvas(element);
    console.log("✅ HTML converted to canvas");

    const imgData = canvas.toDataURL("image/png");

    // 3️⃣ Create PDF
    const pdf = new jsPDF("p", "mm", "a4");
    const imgProps = pdf.getImageProperties(imgData);
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
    pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
    console.log("✅ PDF created");

    // 4️⃣ Convert PDF to blob
    const pdfBlob = pdf.output("blob");
    console.log("✅ PDF converted to blob", pdfBlob);

    // 5️⃣ Prepare FormData
    const formData = new FormData();
    formData.append("files", pdfBlob, `${petName}_prescription.pdf`);
    console.log("✅ PDF appended to FormData");

    const user = JSON.parse(localStorage.getItem("user"));
    console.log("👤 User info:", user);
    formData.append("user_id", user.user_id);

    // 6️⃣ Use React state for phone & pet name
    const normalizedPhone = normalizeIndianPhone(petParentNumber);
    if (!normalizedPhone) {
      alert("Please enter a valid Indian mobile number.");
      return;
    }
    formData.append("pet_parent_phone", normalizedPhone);
    formData.append("pet_name", petName);
    console.log("✅ Pet info appended:", petName, normalizedPhone);

    // 7️⃣ Report type
    const reportType = "Prescription"; // use state
    formData.append("report_type", reportType);
    console.log("✅ Report type appended:", reportType);

    // 8️⃣ Reminder
    const reminderToSend =
      reminderValue === "custom"
        ? `${customReminderNumber} ${customReminderUnit}`
        : reminderValue;
    formData.append("reminder", reminderToSend);
    console.log("✅ Reminder appended:", reminderToSend);

    // 9️⃣ Send to backend
    const res = await axios.post(
      "http://localhost:8000/doctor_upload_file",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    console.log("✅ Response from backend:", res.data);
    alert("Prescription uploaded successfully!");
  } catch (err) {
    console.error("❌ Error in savePrescriptionAndSend:", err);
    alert("Error uploading prescription");
  }
};






  return (
    <div className="doctor-dashboard">
      <nav className="home-nav">
        <div className="home-logo" style={{ display: "flex", alignItems: "center", gap: "30px" }}>
          <a href="#">
            <img src="/PT.png" alt="Doctor Dost Logo" className="logo-image" />
          </a>
        </div>

        <ul className="home-nav-links">
          <li>
            <a className="current-link">Dashboard</a>
          </li>
          <li onClick={() => { navigate("/doctor-records");closeMenu();}}><a>Records</a></li>
        </ul>
      </nav>

      <nav className="phone-mobile-nav">
        <div className="phone-nav-logo">
          <a href="#" className="phone-logo-link">
            <img src="/PT.png" alt="Doctor Dost Logo" className="phone-logo-image" />
          </a>
        </div>

        <button className="phone-hamburger" onClick={toggleMobileMenu}>
          {menuOpen ? '×' : '☰'}
        </button>
      </nav>

      <div className={`phone-mobile-menu ${menuOpen ? 'open' : ''}`}>
        <ul className="home-nav-links">
          <li>
            <a className="current-link">Dashboard</a>
          </li>
          <li onClick={() => { navigate("/doctor-records");closeMenu();}}><a>Records</a></li>
        </ul>
      </div>

      <h1>👨‍⚕️ Welcome, Dr. {doctorName || "Doctor"}</h1>

        <div style={{ marginTop: "15px", display: "flex", gap: "12px" }}>
          <button
            onClick={() => setShowUpdateForm(true)}
            style={{ padding: "10px 15px", borderRadius: "6px", cursor: "pointer" }}
          >
            Update Profile
          </button>

        </div>
         <div style={{ marginTop: "15px", display: "flex", gap: "12px" }}>
              <button
            onClick={() => setSelectedOption("upload")}
            style={{ padding: "10px 15px", borderRadius: "6px", cursor: "pointer" }}
          >
            Upload prescription 
          </button>
          <button
            onClick={() => setSelectedOption("create")}
            style={{ padding: "10px 15px", borderRadius: "6px", cursor: "pointer" }}
          >
            Create prescription 
          </button>

  

        </div>



    

  
      {showUpdateForm && (
        <div className="doctor-update-form-overlay">
          <div className="doctor-update-form">
            <button className="close-btn" onClick={() => setShowUpdateForm(false)}>×</button>

            <h2>Update Your Profile</h2>
            <form onSubmit={(e) => e.preventDefault()}>
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  value={doctorName}
                  onChange={(e) => setDoctorName(e.target.value)}
                  placeholder="Enter full name"
                />
              </div>

              <div className="form-group">
                <label> WhatsApp Phone Number</label>
                <input
                  type="text"
                  value={doctorPhone}
                  onChange={(e) => setDoctorPhone(e.target.value)}
                  placeholder="Enter phone number"
                />
              </div>

                <div className="form-group">
                <label>WhatsApp Number Id</label>
                <input
                  type="text"
                  value={whatsappNumberId}
                  onChange={(e) => setWhatsappNumberId(e.target.value)}
                  placeholder="Enter WhatsApp Access Token"
                />
              </div>

              <div className="form-group">
                <label>WhatsApp Access Token</label>
                <input
                  type="text"
                  value={whatsappAccessToken}
                  onChange={(e) => setWhatsappAccessToken(e.target.value)}
                  placeholder="Enter WhatsApp Access Token"
                />
              </div>

              <div className="form-group">
                <label>Clinic Name</label>
                <input
                  type="text"
                  value={clinicName}
                  onChange={(e) => setClinicName(e.target.value)}
                  placeholder="Enter clinic name"
                />
              </div>

              <button
                type="button"
                onClick={handleDoctorUpdate}
                disabled={isUpdating}
                style={{ marginTop: "10px", padding: "10px 15px" }}
              >
                {isUpdating ? "Updating..." : "Update Profile"}
              </button>

              {updateMessage && (
                <p style={{ marginTop: "10px", color: "green", textAlign: "center" }}>
                  {updateMessage}
                </p>
              )}
            </form>
          </div>
        </div>
      )}

             
      


      {selectedOption === "upload" && (
       <div className="upload-section">
  <form
    onSubmit={async (e) => {
      e.preventDefault();
      const formData = new FormData();
      const fileInput = document.getElementById("reportFile");
      const user = JSON.parse(localStorage.getItem("user"));

      if (fileInput.files.length === 0) {
        alert("Please select a file");
        return;
      }

      for (let i = 0; i < fileInput.files.length; i++) {
        formData.append("files", fileInput.files[i]);
      }

      formData.append("user_id", user.user_id);

      // get & normalize phone
      const rawPhone = document.getElementById("petPhone").value;
      const normalizedPhone = normalizeIndianPhone(rawPhone);
      if (!normalizedPhone) {
        alert("Please enter a valid Indian mobile number.");
        return;
      }

      formData.append("pet_parent_phone", normalizedPhone);
      formData.append("pet_name", document.getElementById("petName").value);

      // ✅ FIX: get report type properly
      const reportTypeEl = document.getElementById("reportType");
      const reportType = reportTypeEl ? reportTypeEl.value : "Unknown";
      formData.append("report_type", reportType);

      // reminder handling
      const reminderToSend =
        reminderValue === "custom"
          ? `${customReminderNumber} ${customReminderUnit}`
          : reminderValue;
      formData.append("reminder", reminderToSend);

      try {
        const res = await axios.post("http://localhost:8000/doctor_upload_file", formData);
        alert("Report uploaded successfully!");
        console.log(res.data);
      } catch (err) {
        alert("Error uploading file");
        console.error(err);
      }
    }}
  >

    <div className="form-group">
      <label>Pet Parent Phone</label>
      <input
        type="tel"
        id="petPhone"
        inputMode="numeric"
        placeholder="e.g. 98765 43210 or +91 9876543210"
        required
        pattern="^(\\+?91[-\\s]?)?[0]?[6-9]\d{9}$"
        title="Enter a valid Indian mobile number"
      />
    </div>

    <div className="form-group">
      <label>Pet Name</label>
      <input type="text" id="petName" placeholder="e.g. Simba" required />
    </div>

    <div className="form-group">
      <label htmlFor="reportType">Report Type</label>
      <select id="reportType" name="reportType">
        <option value="Prescription">Prescription</option>
        <option value="Vaccination">Vaccination</option>
        <option value="Blood Work">Blood Work</option>
      </select>
    </div>

    <div className="form-group">
      <label>Reminder</label>
      <select
        id="reminder"
        value={reminderValue}
        onChange={(e) => setReminderValue(e.target.value)}
      >
        <option value="">Select Reminder</option>
        <option value="15 days">15 days</option>
        <option value="1 month">1 month</option>
        <option value="3 months">3 months</option>
        <option value="6 months">6 months</option>
        <option value="1 year">1 year</option>
        <option value="custom">Custom</option>
      </select>
    </div>

    {reminderValue === "custom" && (
      <div className="form-group">
        <label>Custom Reminder:</label>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <input
            type="number"
            min="1"
            value={customReminderNumber}
            onChange={(e) => setCustomReminderNumber(e.target.value)}
            placeholder="e.g. 45"
            style={{ width: "80px", padding: "6px", borderRadius: "5px", border: "1px solid #ccc" }}
          />
          <select
            value={customReminderUnit}
            onChange={(e) => setCustomReminderUnit(e.target.value)}
            style={{ padding: "6px", borderRadius: "5px", border: "1px solid #ccc" }}
          >
            <option value="days">days</option>
            <option value="months">months</option>
          </select>
        </div>
      </div>
    )}

    <div className="form-group">
      <label>Choose Report File(s)</label>
      <input type="file" id="reportFile" multiple />
    </div>

    <button type="submit" className="upload-button">Upload Report</button>
  </form>
</div>

      )}
      <div
  id="prescription"
  className="printable-prescription"
  style={{
    position: "absolute",
    left: "-9999px",
    top: 0,
    padding: 20,
    fontFamily: "Arial, sans-serif",
    width: 600,
    backgroundColor: "#fff",
  }}
>
  <h1 style={{ textAlign: "center", marginBottom: 20 }}>Prescription</h1>

  <div>
    <strong>Pet Name:</strong> {petName}<br />
    <strong>Pet Parent:</strong> {petParentNumber}<br />
    <strong>Weight:</strong> {weight} kg<br />
    <strong>Temperature:</strong> {temperature} °F
  </div>

  <div style={{ marginTop: 20 }}>
    <strong>Physical Exam:</strong><br />
    Fur: {selectedFur || "N/A"}<br />
    Skin: {selectedSkin || "N/A"}
  </div>

  <div style={{ marginTop: 20 }}>
    <strong>Symptoms:</strong>
    <ul>
      {selectedSymptoms.map((s, i) => <li key={i}>{s}</li>)}
      {otherSymptoms && <li>{otherSymptoms}</li>}
    </ul>
  </div>

  <div style={{ marginTop: 20 }}>
    <strong>Diagnosis:</strong>
    <ul>
      {selectedDiagnosis.map((d, i) => <li key={i}>{d}</li>)}
      {customDiagnosis && <li>{customDiagnosis}</li>}
    </ul>
  </div>

  <div style={{ marginTop: 20 }}>
    <strong>Medicines:</strong>
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th style={{ border: "1px solid #000", padding: 6 }}>Medicine</th>
          <th style={{ border: "1px solid #000", padding: 6 }}>Dosage</th>
          <th style={{ border: "1px solid #000", padding: 6 }}>Duration (days)</th>
        </tr>
      </thead>
      <tbody>
        {medicines.map((med, i) => (
          <tr key={i}>
            <td style={{ border: "1px solid #000", padding: 6 }}>{med.name}</td>
            <td style={{ border: "1px solid #000", padding: 6 }}>{med.dosage}</td>
            <td style={{ border: "1px solid #000", padding: 6 }}>{med.duration}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>

  <div style={{ marginTop: 20 }}>
    <strong>Follow-Up:</strong> {reminderValue === "custom" ? `${customReminderNumber} ${customReminderUnit}` : reminderValue || "N/A"}
  </div>
</div>


      {selectedOption === "create" && (
        <div className="prescription-form">
          <div className="stepper">
            {steps.map((label, index) => (
              <div
                key={index}
                className={`step ${index === step ? "active" : index < step ? "completed" : ""}`}
              >
                {label}
              </div>
            ))}
          </div>

          <div className="step-content">
    
      {step === 0 && (
              <>
              <h3>Basic Details</h3>
          <div className="form-group">
            <label>Pet Name</label>
            <input
              type="text"
              placeholder="e.g. Fluffy"
              value={petName}
              onChange={(e) => setPetName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Pet Parent Number</label>
            <input
              type="text"
              placeholder="e.g. +91 9876543210"
              value={petParentNumber}
              onChange={(e) => setPetParentNumber(e.target.value)}
            />
          </div>
          <h3>Vitals</h3>
          <div className="form-group">
            <label>Weight (kg)</label>
            <input
              type="number"
              placeholder="e.g. 12"
              step="0.1"
              value={weight}
              onChange={(e) => {
                let val = parseFloat(e.target.value);
                if (val < 0) val = 0;
                if (val > 100) val = 100;
                setWeight(val);
              }}
            />
          </div>

          <div className="form-group">
            <label>Temperature (°F)</label>
            <input
              type="number"
              placeholder="e.g. 101.3"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              onBlur={() => {
                let val = parseFloat(temperature);
                if (val < 90) val = 90;
                if (val > 105) val = 105;
                setTemperature(val);
              }}
            />
          </div>
        </>
      )}

            {step === 1 && (
        <>
          <h3>Physical Exam</h3>

          <div className="chip-group">
            <label>Fur/Coat Condition</label>
            {['Dry', 'Oily', 'Wet', 'Matted', 'Shedding', 'Bald patches'].map((item) => (
              <button
                key={item}
                className={`chip ${selectedFur === item ? 'selected' : ''}`}
                onClick={() => setSelectedFur(item)}
              >
                {item}
              </button>
            ))}
          </div>

          <div className="chip-group">
            <label>Skin Condition</label>
              {['Normal', 'Rash', 'Redness', 'Allergic', 'Fungal signs', 'Parasites visible'].map((item) => (
                <button
                  key={item}
                  className={`chip ${selectedSkin === item ? 'selected' : ''}`}
                  onClick={() => setSelectedSkin(item)}
                >
                  {item}
                </button>
              ))}
                </div>
              </>
            )}

            {step === 2 && (
              <>
                <h3>Symptoms</h3>

                <div className="chip-group">
                  <label style={{ display: "block", marginBottom: 6 }}>Quick Multi-Select</label>
                  {SYMPTOMS.map((symptom) => {
                    const active = selectedSymptoms.includes(symptom);
                    return (
                      <button
                        type="button"
                        key={symptom}
                        className={`chip ${active ? "active" : ""}`}
                        onClick={() => toggleSymptom(symptom)}
                        aria-pressed={active}
                      >
                        {symptom}
                      </button>
                    );
                  })}
                </div>

                <div className="form-group">
                  <label>Others (Free text)</label>
                  <input
                    type="text"
                    placeholder="Describe other symptoms"
                    value={otherSymptoms}
                    onChange={(e) => setOtherSymptoms(e.target.value)}
                  />
                  <span className="hint">Optional — add anything not covered above</span>
                </div>
              </>
            )}

           {step === 3 && (
        <>
          <h3>Diagnosis</h3>
          <div className="chip-group">
            {allDiagnoses.map((diag) => (
              <button
                key={diag}
                className={`chip ${selectedDiagnosis.includes(diag) ? 'selected' : ''}`}
                onClick={() => toggleDiagnosis(diag)}
              >
                {diag}
              </button>
            ))}
          </div>

          <div className="custom-diagnosis">
            <input
              type="text"
              placeholder="Add custom diagnosis"
              value={customDiagnosis}
              onChange={(e) => setCustomDiagnosis(e.target.value)}
            />
            <button type="button" onClick={addCustomDiagnosis}>
              Add
            </button>
          </div>
        </>
      )}

      {step === 4 && (
        <div className="prescription-step">
          <h3>Prescription</h3>
          {medicines.map((med, index) => (
            <div className="prescription-medicine-row" key={index}>
              <input
                type="text"
                placeholder="Medicine name"
                value={med.name}
                onChange={(e) => updateMedicine(index, "name", e.target.value)}
                className="prescription-input"
              />
              <select
                value={med.dosage}
                onChange={(e) => updateMedicine(index, "dosage", e.target.value)}
                className="prescription-select"
              >
                <option value="once a day">Once a day</option>
                <option value="twice a day">Twice a day</option>
                <option value="thrice a day">Thrice a day</option>
              </select>
              <input
                type="number"
                placeholder="Duration (days)"
                value={med.duration}
                onChange={(e) => updateMedicine(index, "duration", e.target.value)}
                min="1"
                className="prescription-input"
              />
            </div>
          ))}
          <button type="button" className="prescription-add-btn" onClick={addMedicine}>
            Add Medicine
          </button>
        </div>
      )}

           {step === 5 && (
        <div className="followup-step">
          <h3>Follow-Up</h3>
          <div className="form-group">
            <label>Reminder</label>
            <select
              id="reminder"
              value={reminderValue}
              onChange={(e) => setReminderValue(e.target.value)}
              className="followup-select"
            >
              <option value="">Select Reminder</option>
              <option value="15 days">15 days</option>
              <option value="1 month">1 month</option>
              <option value="3 months">3 months</option>
              <option value="6 months">6 months</option>
              <option value="1 year">1 year</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          {reminderValue === "custom" && (
            <div className="form-group custom-reminder">
              <label>Custom Reminder:</label>
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <input
                  type="number"
                  min="1"
                  value={customReminderNumber}
                  onChange={(e) => setCustomReminderNumber(e.target.value)}
                  placeholder="e.g. 45"
                  className="custom-reminder-input"
                />
                <select
                  value={customReminderUnit}
                  onChange={(e) => setCustomReminderUnit(e.target.value)}
                  className="custom-reminder-select"
                >
                  <option value="days">days</option>
                  <option value="months">months</option>
                </select>
              </div>
            </div>
          )}
        </div>
      )}
          </div>

          <div className="form-navigation">
            {step > 0 && <button onClick={prevStep}>Back</button>}
            {step < steps.length - 1 && <button onClick={nextStep}>Next</button>}
            {step === steps.length - 1 && <button type="submit" onClick={savePrescriptionAndSend}>Save Prescription</button>}
          </div>
        </div>
      )}
  


    </div>
  );
};

export default DoctorDashboard;
