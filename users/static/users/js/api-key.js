document.addEventListener("DOMContentLoaded", () => {
  const getKeyBtn = document.getElementById("get-key-btn");
  const refreshKeyBtn = document.getElementById("refresh-key-btn");
  const apiKeyDisplay = document.getElementById("api-key-display");

  const getCSRFToken = () => {
    const cookie = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="));
    return cookie ? cookie.split("=")[1] : "";
  };

  const updateUIWithKey = (key) => {
  apiKeyDisplay.textContent = "🔑 Your API key: " + key;
  apiKeyDisplay.style.display = "block";
  apiKeyDisplay.style.color = "#1a1a1a";
  getKeyBtn.style.display = "none";
  refreshKeyBtn.style.display = "inline-block";
    };

  const showError = (message) => {
  apiKeyDisplay.textContent = "❌ Error: " + message;
  apiKeyDisplay.style.display = "block"; 
  apiKeyDisplay.style.color = "darkred";
    };

  getKeyBtn.addEventListener("click", async () => {
    try {
      const response = await fetch(getOrCreateAPIKey, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      const data = await response.json();
      if (response.ok) {
        updateUIWithKey(data.api_key);
      } else {
        showError(data.detail || "Could not get API key");
      }
    } catch (err) {
      showError("Request failed");
    }
  });

  refreshKeyBtn.addEventListener("click", async () => {
    try {
      const response = await fetch(refreshAPIKey, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      const data = await response.json();
      if (response.ok) {
        updateUIWithKey(data.api_key);
      } else {
        showError(data.detail || "Could not refresh API key");
      }
    } catch (err) {
      showError("Refresh request failed");
    }
  });
});
