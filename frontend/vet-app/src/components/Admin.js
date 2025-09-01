import React, { useState, useEffect } from "react";

const AdminPage = () => {
  const [reminders, setReminders] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);

  // Fetch today's reminders
  useEffect(() => {
    fetch("/api/reminders_today")
      .then((res) => res.json())
      .then((data) => {
        console.log("Reminders API response:", data);  // debug log
      setReminders(Array.isArray(data) ? data : data.data || []);
        })
      .catch((err) => console.error("Error fetching reminders:", err));
  }, []);

  // Fetch allowed doctors
  useEffect(() => {
    fetch("/api/allowed_doctors")
      .then((res) => res.json())
      .then((data) => setDoctors(data))
      .catch((err) => console.error("Error fetching doctors:", err));
  }, []);

  // Add doctor email
  const handleAddDoctor = async (e) => {
    e.preventDefault();

    const res = await fetch("/api/allowed_doctors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    if (res.ok) {
      const newDoctor = await res.json();
      setDoctors([...doctors, newDoctor]);
      setEmail("");
    } else {
      alert("Error adding doctor!");
    }
  };

  // Delete doctor email
  const handleDeleteDoctor = async (id) => {
    const res = await fetch(`/api/allowed_doctors/${id}`, {
      method: "DELETE",
    });

    if (res.ok) {
      setDoctors(doctors.filter((doc) => doc.id !== id));
    } else {
      alert("Error deleting doctor!");
    }
  };
  const handleSendReminders = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/send_tomorrow_reminders", {
        method: "POST",
      });
      if (res.ok) {
        alert("✅ Reminders sent successfully!");
      } else {
        alert("❌ Failed to send reminders");
      }
    } catch (err) {
      console.error("Error sending reminders:", err);
      alert("❌ Error sending reminders");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-10">
      {/* Section 1: Today's Reminders */}
      <section>
        <h2 className="text-2xl font-bold mb-4">Reminders for Today</h2>
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-200">
              <th className="border border-gray-300 px-4 py-2">Pet Name</th>
              <th className="border border-gray-300 px-4 py-2">Doctor</th>
              <th className="border border-gray-300 px-4 py-2">Clinic</th>
              <th className="border border-gray-300 px-4 py-2">Reminder Date</th>
            </tr>
          </thead>
          <tbody>
            {reminders.map((rem, idx) => (
              <tr key={idx}>
                <td className="border border-gray-300 px-4 py-2">{rem.pet_name}</td>
                <td className="border border-gray-300 px-4 py-2">{rem.doctor_name}</td>
                <td className="border border-gray-300 px-4 py-2">{rem.clinic_name}</td>
                <td className="border border-gray-300 px-4 py-2">
                  {new Date(rem.reminder_at).toLocaleDateString("en-GB", {
                    day: "2-digit",
                    month: "short",
                    year: "2-digit",
                  })}
                </td>
              </tr>
            ))}
            {reminders.length === 0 && (
              <tr>
                <td colSpan="4" className="text-center py-4 text-gray-500">
                  No reminders for today.
                </td>
              </tr>
            )}
          </tbody>
        </table>
                  <button
            onClick={handleSendReminders}
            disabled={loading}
            className={`px-4 py-2 rounded-md text-white ${
              loading ? "bg-gray-400 cursor-not-allowed" : "bg-green-600 hover:bg-green-700"
            }`}
          >
            {loading ? "Sending..." : "Send Reminders"}
          </button>
      </section>

      {/* Section 2: Allowed Doctors Management */}
      <section>
        <h2 className="text-2xl font-bold mb-4">Allowed Doctors</h2>

        {/* Add Doctor Form */}
        <form onSubmit={handleAddDoctor} className="flex gap-2 mb-6">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter doctor Gmail"
            required
            className="border px-3 py-2 rounded-md w-72"
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Add
          </button>
        </form>

        {/* Doctors Table */}
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-200">
              <th className="border border-gray-300 px-4 py-2">ID</th>
              <th className="border border-gray-300 px-4 py-2">Doctor Email</th>
              <th className="border border-gray-300 px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {doctors.map((doc) => (
              <tr key={doc.id}>
                <td className="border border-gray-300 px-4 py-2">{doc.id}</td>
                <td className="border border-gray-300 px-4 py-2">{doc.email}</td>
                <td className="border border-gray-300 px-4 py-2">
                  <button
                    onClick={() => handleDeleteDoctor(doc.id)}
                    className="bg-red-500 text-white px-3 py-1 rounded-md hover:bg-red-600"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {doctors.length === 0 && (
              <tr>
                <td colSpan="3" className="text-center py-4 text-gray-500">
                  No doctors added yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
};

export default AdminPage;
