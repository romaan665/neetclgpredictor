console.log("JS LOADED ✅");

/* ================= GLOBAL ================= */
let LAST_PREDICTION_DATA = null;

/* ================= AUTH HELPERS ================= */
function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem("neetUser"));
  } catch {
    return null;
  }
}

function setCurrentUser(user) {
  if (user) localStorage.setItem("neetUser", JSON.stringify(user));
  else localStorage.removeItem("neetUser");
}

/* ================= PREDICTOR ================= */
function initPredictorUI() {
  const predictForm = document.getElementById("predictForm");
  if (!predictForm) return;

  predictForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const user = getCurrentUser();
    if (!user || !user.id) {
      alert("Please login first");
      return;
    }

    const formData = {
      rank: parseInt(document.getElementById("rank").value),
      category: document.getElementById("category").value,
      quota: document.getElementById("quota").value,
      state: document.getElementById("state").value,
      course: document.getElementById("course").value
    };

    const btn = document.getElementById("predictBtn");
    const spinner = document.getElementById("spinner");
    const btnText = document.getElementById("btnText");

    btn.disabled = true;
    spinner.classList.remove("hidden");
    btnText.textContent = "Predicting...";


    try {
      const response = await fetch("/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": user.id   // ✅ REQUIRED FIX
        },
        body: JSON.stringify({
          air_rank: formData.rank,
          course: formData.course,
          category: formData.category,
          quota: formData.quota,
          state: formData.state
        })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Prediction failed");

      displayResults({
        round1: data.results.round_1.map(c => ({
          college: c.INSTITUTE,
          quota: formData.quota,
          chance: c.chance,
          rank_range: c.predicted_closing_rank
        })),
        round2: data.results.round_2.map(c => ({
          college: c.INSTITUTE,
          quota: formData.quota,
          chance: c.chance,
          rank_range: c.predicted_closing_rank
        })),
        round3: data.results.round_3.map(c => ({
          college: c.INSTITUTE,
          quota: formData.quota,
          chance: c.chance,
          rank_range: c.predicted_closing_rank
        })),
        no_chance: data.results.no_chance.map(c => ({
          college: c.INSTITUTE,
          quota: formData.quota,
          chance: c.chance,
          rank_range: c.predicted_closing_rank
        }))
      });

    } catch (err) {
      alert(err.message);
    } finally {
      btn.disabled = false;
      spinner.classList.add("hidden");
      btnText.textContent = "Predict My Colleges";
    }

  });
}

/* ================= RESULTS ================= */
function displayResults(data) {
  LAST_PREDICTION_DATA = data;

  document.getElementById("round1Count").textContent = data.round1.length;
  document.getElementById("round2Count").textContent = data.round2.length;
  document.getElementById("round3Count").textContent = data.round3.length;
  document.getElementById("noChanceCount").textContent = data.no_chance.length;

  displayCollegeList("round1List", data.round1, "emerald");
  displayCollegeList("round2List", data.round2, "blue");
  displayCollegeList("round3List", data.round3, "orange");
  displayCollegeList("noChanceList", data.no_chance, "red");

  // ✅ SHOW results section
  const resultsSection = document.getElementById("resultsSection");
  resultsSection.classList.remove("hidden");

  // ✅ INIT TILE CLICK LOGIC *AFTER* RESULTS EXIST
  initResultTiles();

  // ✅ AUTO-OPEN ROUND 1
  setTimeout(() => {
    document.getElementById("tileRound1")?.click();
  }, 50);

  addDownloadButton(resultsSection);
}



function displayCollegeList(id, colleges, color) {
  const el = document.getElementById(id);
  if (!el) return;

  el.innerHTML = colleges.map(c => `
    <div class="college-card border-l-${color}-500">
      <div>
        <div class="font-bold">${c.college}</div>
        <div class="text-sm">${c.quota} - ${c.chance}</div>
      </div>
      <div class="font-bold">${c.rank_range}</div>
    </div>
  `).join("");
}
// ---------------- FORGOT PASSWORD ----------------
const forgotForm = document.getElementById("forgotForm");

if (forgotForm) {
  forgotForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const msg = document.getElementById("msg");

    try {
      const res = await fetch("http://127.0.0.1:8000/forgot-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email })
      });

      const data = await res.json();

      msg.textContent = "If email exists, reset link sent 📩";
      msg.className = "text-green-600";

      console.log("FORGOT RESPONSE:", data);

    } catch (err) {
      console.error(err);
      msg.textContent = "Something went wrong ❌";
      msg.className = "text-red-600";
    }
  });
}


// ---------------- RESET PASSWORD ----------------
const resetBtn = document.querySelector("button");

if (resetBtn && window.location.pathname.includes("reset-password")) {
  resetBtn.addEventListener("click", async () => {
    const password = document.getElementById("newPassword").value;
    const msg = document.getElementById("msg");

    const token = new URLSearchParams(window.location.search).get("token");

    try {
      const res = await fetch("http://127.0.0.1:8000/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          token: token,
          new_password: password
        })
      });

      const data = await res.json();

      if (res.ok) {
        msg.textContent = "Password reset successful ✅";
        msg.className = "text-green-600";
      } else {
        msg.textContent = data.detail;
        msg.className = "text-red-600";
      }

    } catch (err) {
      console.error(err);
      msg.textContent = "Error resetting password ❌";
    }
  });
}

/* ================= DOWNLOAD PDF ================= */

function addDownloadButton(resultsSection) {
  if (!resultsSection) return;

  const oldBtn = document.getElementById("downloadPDFBtn");
  if (oldBtn) oldBtn.remove();

  const btn = document.createElement("button");
  btn.id = "downloadPDFBtn";
  btn.textContent = "📥 Download PDF Report";
  btn.className =
    "mt-8 w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 rounded-xl shadow-lg";

  btn.onclick = () => {
    if (!LAST_PREDICTION_DATA) {
      alert("No prediction data available");
      return;
    }
    generatePDF(LAST_PREDICTION_DATA);
  };

  resultsSection.appendChild(btn);
}

/* ================= BUILD TABLE ================= */

function buildTable(rows) {
  if (!rows || rows.length === 0) {
    return "<p style='color:#666'>No data available</p>";
  }

  return `
    <table style="width:100%; border-collapse:collapse; margin-bottom:16px;"
           border="1" cellpadding="6">
      <thead>
        <tr style="background:#f3f4f6;">
          <th align="left">College</th>
          <th align="left">Quota</th>
          <th align="left">Chance</th>
          <th align="right">Rank</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td>${r.college}</td>
            <td>${r.quota}</td>
            <td>${r.chance}</td>
            <td align="right">${r.rank_range}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

/* ================= GENERATE PDF ================= */

function generatePDF(data) {
  const { jsPDF } = window.jspdf;

  if (!jsPDF) {
    alert("jsPDF not loaded");
    return;
  }

  if (!data || (!data.round1 && !data.round2)) {
    alert("No data to export");
    return;
  }

  const doc = new jsPDF("p", "mm", "a4");
  let y = 15;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.text("NEET College Prediction Report", 105, y, { align: "center" });
  y += 10;

  function section(title, rows) {
    if (!rows || rows.length === 0) return;

    doc.setFontSize(13);
    doc.setFont("helvetica", "bold");
    doc.text(title, 14, y);
    y += 6;

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");

    rows.forEach((r, i) => {
      if (y > 270) {
        doc.addPage();
        y = 15;
      }

      doc.text(`${i + 1}. ${r.college}`, 14, y); y += 5;
      doc.text(`Quota: ${r.quota}`, 18, y); y += 5;
      doc.text(`Chance: ${r.chance}`, 18, y); y += 5;
      doc.text(`Predicted Rank: ${r.rank_range}`, 18, y); y += 7;
    });

    y += 5;
  }

  section("Round 1 – Guaranteed", data.round1);
  section("Round 2 – Possible", data.round2);
  section("Round 3 – Maybe", data.round3);
  section("No Chance", data.no_chance);

  doc.save("NEET-Prediction.pdf");
}


/* ================= NAVBAR ================= */
function refreshNavbar() {
  const user = getCurrentUser();

  const navLogin  = document.getElementById("navLogin");
  const navSignup = document.getElementById("navSignup");
  const navUser   = document.getElementById("navUser");
  const navLogout = document.getElementById("navLogout");

  if (!navLogin || !navSignup || !navUser || !navLogout) return;

  if (user && user.name) {
    navLogin.style.display = "none";
    navSignup.style.display = "none";
    navUser.textContent = `Hi, ${user.name}`;
    navUser.classList.remove("hidden");
    navLogout.classList.remove("hidden");
  } else {
    navLogin.style.display = "";
    navSignup.style.display = "";
    navUser.classList.add("hidden");
    navLogout.classList.add("hidden");
  }
}
/* ================= DARK MODE ================= */
document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");
  const html = document.documentElement;

  if (!themeToggle || !themeIcon) return; // pages without toggle

  // Load saved theme
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    html.classList.add("dark");
    themeIcon.textContent = "🌙";
    themeIcon.classList.add("translate-x-7");
    themeIcon.classList.remove("translate-x-1");
  }

  themeToggle.addEventListener("click", () => {
    const isDark = html.classList.toggle("dark");

    if (isDark) {
      themeIcon.textContent = "🌙";
      themeIcon.classList.add("translate-x-7");
      themeIcon.classList.remove("translate-x-1");
      localStorage.setItem("theme", "dark");
    } else {
      themeIcon.textContent = "☀";
      themeIcon.classList.add("translate-x-1");
      themeIcon.classList.remove("translate-x-7");
      localStorage.setItem("theme", "light");
    }
  });
});

/* ================= DOM READY ================= */
document.addEventListener("DOMContentLoaded", () => {
  refreshNavbar();
  initPredictorUI();
  initResultTiles();

  /* SIGNUP */
  document.getElementById("signupForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const res = await fetch("/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: suName.value.trim(),
        email: suEmail.value.trim(),
        phone: suPhone.value.trim(),
        password: suPassword.value,
        neet_marks: parseInt(neetMarks.value),
        hsc_marks: parseInt(hscMarks.value),
        percentage: parseFloat(percentage.value),
        registration_date: registrationDate.value,
        passing_year: parseInt(passingYear.value)
      })
    });

    const data = await res.json();
    if (!res.ok) return alert(data.detail || "Signup failed");

    alert("Signup successful!");
    location.href = "/login";
  });

  /* LOGIN */
  document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const res = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: liEmail.value.trim(),
        password: liPassword.value
      })
    });

    const data = await res.json();
    if (!res.ok) return alert(data.detail || "Login failed");

    setCurrentUser(data.user);
    location.href = "/";
  });

  document.getElementById("navLogout")?.addEventListener("click", () => {
    setCurrentUser(null);
    location.href = "/";
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("abbrToggle");
  const content = document.getElementById("abbrContent");
  const icon = document.getElementById("abbrIcon");

  if (!toggle || !content || !icon) return;

  toggle.addEventListener("click", () => {
    const expanded = content.classList.contains("opacity-100");

    if (expanded) {
      content.style.maxHeight = "0px";
      content.classList.remove("opacity-100");
      content.classList.add("opacity-0");
      icon.style.transform = "rotate(0deg)";
    } else {
      content.style.maxHeight = content.scrollHeight + "px";
      content.classList.remove("opacity-0");
      content.classList.add("opacity-100");
      icon.style.transform = "rotate(180deg)";
    }
  });
});
function initResultTiles() {
  const tiles = document.querySelectorAll(".result-tile");
  const blocks = document.querySelectorAll(".result-block");

  tiles.forEach(tile => {
    tile.addEventListener("click", () => {
      const targetId = tile.dataset.target;

      // hide all result blocks
      blocks.forEach(b => b.classList.add("hidden"));

      // remove active state from tiles
      tiles.forEach(t => t.classList.remove("ring-4", "ring-white"));

      // show selected block
      const target = document.getElementById(targetId);
      if (target) {
        target.classList.remove("hidden");
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      // highlight active tile
      tile.classList.add("ring-4", "ring-white");
    });
  });
}
const hscMarksInput = document.getElementById("hscMarks");
const percentageInput = document.getElementById("percentage");

// assuming HSC is out of 600 (change if needed)
hscMarksInput?.addEventListener("input", () => {
  const marks = parseFloat(hscMarksInput.value);
  if (!isNaN(marks)) {
    const percent = (marks / 600) * 100;
    percentageInput.value = percent.toFixed(2);
  }
});
