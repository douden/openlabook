document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".admonition.fullscreenable").forEach(admonition => {
    const header = admonition.querySelector("p.admonition-title");
    if (!header) return;

    // Avoid inserting multiple buttons
    if (header.querySelector(".fullscreen-btn")) return;

    const btn = document.createElement("button");
    btn.className = "fullscreen-btn";
    btn.innerHTML = '<i class="fas fa-expand"></i>';
    btn.onclick = function () {
       const details = admonition.querySelector("section details");
      if (admonition.classList.contains("fullscreen")) {
        admonition.classList.remove("fullscreen");
        const grasple = details.querySelector(".grasplecontainer");
        grasple.style.height = `400px`;
      } else {
        admonition.classList.add("fullscreen");
        // Open details if not already open
        if (details && !details.hasAttribute("open")) {
        details.setAttribute("open", "");
        }
        if (details) {
          // Measure available height
          const detailsRect = admonition.getBoundingClientRect();
          const summary = details.querySelector("summary");
          const summaryRect = summary.getBoundingClientRect();
          const remainder = detailsRect.height -summaryRect.bottom;
          const grasple = details.querySelector(".grasplecontainer");
          grasple.style.height = `calc(${remainder}px + 1.5rem)`;
        }
      }
    };

    // Style the button into the title bar
    header.style.position = "relative";
    btn.style.position = "absolute";
    btn.style.right = "0.5em";
    btn.style.top = "0.2em";

    header.appendChild(btn);
  });
});
