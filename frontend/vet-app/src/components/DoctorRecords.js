import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./DoctorRecords.css";

const DoctorRecords = ({ profile }) => {
  const doctorId =
    profile?.user_id ||
    JSON.parse(localStorage.getItem("user") || "{}")?.user_id;

  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchDate, setSearchDate] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [expanded, setExpanded] = useState({});
  const [error, setError] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    const fetchDoctorRecords = async () => {
      if (!doctorId) {
        setError("Doctor id not available");
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const res = await axios.get(`http://localhost:8000/doctor_reports/${doctorId}`);
        const serverReports = res.data?.reports ?? [];

        // 🔑 Use secure_doctor_link directly
        const updatedReports = serverReports.map(report => ({
          ...report,
          report_pdf_links: report.report_pdf_links || [],
          protected_link: report.secure_doctor_link || null
        }));

        setRecords(updatedReports);
      } catch (err) {
        console.error("Error fetching doctor records:", err);
        setError(err.response?.data?.detail || err.message || "Failed to fetch records");
      } finally {
        setLoading(false);
      }
    };
    fetchDoctorRecords();
  }, [doctorId]);

  const formatDate = (val) => {
    if (!val) return "N/A";
    try {
      const d = new Date(val);
      if (isNaN(d.getTime())) return String(val);
      return d.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return String(val);
    }
  };

  const filteredRecords = useMemo(() => {
    const st = searchTerm.trim().toLowerCase();
    return (records || []).filter((rec) => {
      const matchesSearch =
        !st ||
        (rec.pet_name || "").toLowerCase().includes(st) ||
        (rec.pet_parent_phone || "").toLowerCase().includes(st);

      const matchesDate =
        !searchDate ||
        (rec.reminder && String(rec.reminder).slice(0, 10) === searchDate);

      const matchesType =
        !typeFilter || (rec.report_type || "").toLowerCase() === typeFilter.toLowerCase();

      return matchesSearch && matchesDate && matchesType;
    });
  }, [records, searchTerm, searchDate, typeFilter]);

  if (loading) return <div className="loader">Loading...</div>;

  const toggleMobileMenu = () => setMenuOpen(prev => !prev);

  return (
    <div className="doctor-dashboard">
      <nav className="home-nav">
        <div className="home-logo">
          <a href="/"><img src="/PT.png" alt="Logo" className="logo-image" /></a>
        </div>
        <ul className="home-nav-links">
          <li onClick={() => navigate("/doctor")}><a>Dashboard</a></li>
          <li><a className="current-link">Records</a></li>
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
          <li onClick={() => navigate("/doctor")}><a>Dashboard</a></li>
          <li><a className="current-link">Records</a></li>
        </ul>
      </div>

      <section className="doctor-section">
        <h2>Doctor Uploaded Records</h2>

        <div className="filter-bar">
          <input
            type="text"
            placeholder="Search by pet name or owner phone..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <input
            type="date"
            value={searchDate}
            onChange={(e) => setSearchDate(e.target.value)}
            className="date-input"
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="type-input"
            title="Filter by report type"
          >
            <option value="">All Types</option>
            <option value="Prescription">Prescription</option>
            <option value="Vaccination">Vaccination</option>
            <option value="Blood Work">Blood Work</option>
          </select>
        </div>

        {error && <p className="error-text">Error: {String(error)}</p>}

        {filteredRecords.length === 0 ? (
          <p>No doctor records found.</p>
        ) : (
          <div className="record-list">
            {filteredRecords.map((rec, idx) => (
              <div key={rec.report_id ?? idx} className="record-card">
                <div className="record-header">
                  <span className={`type-badge type-${(rec.report_type || "Unknown").replace(/\s+/g, "-").toLowerCase()}`}>
                    {rec.report_type || "Unknown"}
                  </span>
                  <span className="created-at">
                    Created: {formatDate(rec.created_at)}
                  </span>
                </div>

                <p><strong>Pet Name:</strong> {rec.pet_name ?? "N/A"}</p>
                <p><strong>Owner Phone:</strong> {rec.pet_parent_phone ?? "N/A"}</p>
                <p><strong>Reminder Date:</strong> {rec.reminder ? String(rec.reminder).slice(0,10) : "N/A"}</p>
                <p><strong>Secure Link:</strong> {rec.protected_link ? <a href={rec.protected_link} target="_blank" rel="noreferrer">Open</a> : "N/A"}</p>

                
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default DoctorRecords;
