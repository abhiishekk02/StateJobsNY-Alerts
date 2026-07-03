const ROLES = ["Software & IT", "Data & Analytics", "Business & Operations", "Engineering", "Finance", "Communications"];
const LOCATIONS = ["Albany", "New York City", "Buffalo", "Rochester", "Syracuse", "Remote / statewide"];

function makeChips(containerId, name, values) {
  const root = document.getElementById(containerId);
  values.forEach((value) => {
    const label = document.createElement("label");
    label.className = "chip";
    const input = document.createElement("input");
    input.type = "checkbox"; input.name = name; input.value = value;
    const text = document.createElement("span"); text.textContent = value;
    label.append(input, text); root.append(label);
  });
}

makeChips("role-chips", "roles", ROLES);
makeChips("location-chips", "locations", LOCATIONS);
const year = new Date().getFullYear();
const select = document.getElementById("graduation-year");
for (let value = year + 2; value >= year - 10; value--) select.add(new Option(String(value), String(value)));

const form = document.getElementById("subscribe-form");
const status = document.getElementById("form-status");
form.addEventListener("submit", async (event) => {
  event.preventDefault(); status.className = "form-status"; status.textContent = "";
  const data = new FormData(form);
  const payload = {
    name: data.get("name")?.trim(), email: data.get("email")?.trim(),
    graduationYear: Number(data.get("graduationYear")), roles: data.getAll("roles"),
    locations: data.getAll("locations"), consent: data.get("consent") === "on",
  };
  if (!form.reportValidity() || !payload.roles.length || !payload.locations.length) {
    status.className = "form-status error"; status.textContent = "Please complete each step and choose at least one role and location."; return;
  }
  const button = form.querySelector("button[type=submit]"); button.disabled = true; button.firstElementChild.textContent = "Creating your alert…";
  try {
    if (!window.NORTHSTAR_API_URL) throw new Error("Alerts are not connected yet. Please check back shortly.");
    const response = await fetch(`${window.NORTHSTAR_API_URL}/api/subscribe`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || "We couldn’t create your alert. Please try again.");
    form.reset(); status.className = "form-status success"; status.textContent = "You’re almost there. Check your inbox to confirm your email.";
  } catch (error) { status.className = "form-status error"; status.textContent = error.message; }
  finally { button.disabled = false; button.firstElementChild.textContent = "Start my alerts"; }
});

const observer = new IntersectionObserver((entries) => entries.forEach((entry) => entry.isIntersecting && entry.target.classList.add("visible")), {threshold: .12});
document.querySelectorAll(".principles article, .join-intro, .form-card").forEach((element) => observer.observe(element));
