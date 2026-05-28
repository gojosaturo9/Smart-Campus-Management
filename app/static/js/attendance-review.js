document.querySelectorAll("[data-attendance-review-modal]").forEach((modal) => {
  const counts = {
    total: modal.querySelector('[data-review-count="total"]'),
    present: modal.querySelector('[data-review-count="present"]'),
    absent: modal.querySelector('[data-review-count="absent"]'),
  };
  const statusSelects = Array.from(modal.querySelectorAll("[data-review-status-select]"));

  const statusLabel = (status) => (status === "present" ? "Present" : "Absent");
  const statusIcon = (status) => (status === "present" ? "&#10003;" : "!");
  const manualLabel = (fromStatus, toStatus) => {
    if (fromStatus === toStatus) {
      return "AI result";
    }
    return toStatus === "present" ? "Manual Present" : "Manual Absent";
  };

  const updateRow = (select) => {
    const row = select.closest(".attendance-review-row");
    if (!row) {
      return;
    }
    const aiStatus = row.dataset.aiStatus || "absent";
    const finalStatus = select.value === "present" ? "present" : "absent";
    const note = manualLabel(aiStatus, finalStatus);
    const reasonInput = row.querySelector("[data-review-reason]");
    const noteNode = row.querySelector("[data-review-manual-note]");
    const pill = row.querySelector("[data-review-ai-pill]");

    row.dataset.finalStatus = finalStatus;
    row.classList.toggle("is-present", finalStatus === "present");
    row.classList.toggle("is-absent", finalStatus === "absent");
    row.classList.toggle("is-manual", aiStatus !== finalStatus);

    if (reasonInput) {
      reasonInput.value = aiStatus === finalStatus ? "" : note;
    }
    if (noteNode) {
      noteNode.textContent = note;
      noteNode.classList.toggle("is-manual", aiStatus !== finalStatus);
    }
    if (pill) {
      pill.classList.toggle("present", finalStatus === "present");
      pill.classList.toggle("absent", finalStatus === "absent");
      pill.innerHTML = `<span class="attendance-state-icon">${statusIcon(finalStatus)}</span><span>${statusLabel(finalStatus)}</span>`;
    }
  };

  const updateCounts = () => {
    const totals = {
      total: statusSelects.length,
      present: 0,
      absent: 0,
    };

    statusSelects.forEach((select) => {
      if (select.value in totals) {
        totals[select.value] += 1;
      }
    });

    Object.entries(totals).forEach(([key, value]) => {
      if (counts[key]) {
        counts[key].textContent = String(value);
      }
    });
  };

  statusSelects.forEach((select) => {
    select.addEventListener("change", () => {
      updateRow(select);
      updateCounts();
    });
    updateRow(select);
  });

  updateCounts();
});
