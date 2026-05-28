(() => {
  const modal = document.querySelector("[data-photo-adjust-modal]");
  if (!modal || !window.DataTransfer) {
    return;
  }

  const canvas = modal.querySelector("[data-photo-adjust-canvas]");
  const zoomInput = modal.querySelector("[data-photo-adjust-zoom]");
  const xInput = modal.querySelector("[data-photo-adjust-x]");
  const yInput = modal.querySelector("[data-photo-adjust-y]");
  const resetButton = modal.querySelector("[data-photo-adjust-reset]");
  const saveButton = modal.querySelector("[data-photo-adjust-save]");
  const cancelButton = modal.querySelector("[data-photo-adjust-cancel]");
  const context = canvas.getContext("2d");

  let activeInput = null;
  let activeImage = null;
  let objectUrl = "";

  const state = {
    zoom: 1,
    offsetX: 0,
    offsetY: 0,
  };

  const resetControls = () => {
    state.zoom = 1;
    state.offsetX = 0;
    state.offsetY = 0;
    zoomInput.value = "1";
    xInput.value = "0";
    yInput.value = "0";
  };

  const draw = () => {
    if (!activeImage) {
      return;
    }

    const size = canvas.width;
    const coverScale = Math.max(size / activeImage.width, size / activeImage.height);
    const scale = coverScale * state.zoom;
    const drawWidth = activeImage.width * scale;
    const drawHeight = activeImage.height * scale;
    const maxX = Math.max(0, (drawWidth - size) / 2);
    const maxY = Math.max(0, (drawHeight - size) / 2);
    const x = (size - drawWidth) / 2 + state.offsetX * maxX;
    const y = (size - drawHeight) / 2 + state.offsetY * maxY;

    context.clearRect(0, 0, size, size);
    context.fillStyle = "#f6f9fc";
    context.fillRect(0, 0, size, size);
    context.drawImage(activeImage, x, y, drawWidth, drawHeight);
  };

  const closeModal = () => {
    modal.hidden = true;
    document.body.classList.remove("photo-adjust-open");
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = "";
    }
    activeImage = null;
  };

  const openModal = (input, file) => {
    activeInput = input;
    activeImage = new Image();
    objectUrl = URL.createObjectURL(file);
    resetControls();

    activeImage.onload = () => {
      modal.hidden = false;
      document.body.classList.add("photo-adjust-open");
      draw();
    };
    activeImage.onerror = () => {
      closeModal();
      input.value = "";
      window.alert("Upload a valid image file.");
    };
    activeImage.src = objectUrl;
  };

  const setAdjustedFile = (blob) => {
    const dataTransfer = new DataTransfer();
    const file = new File([blob], "profile-photo.jpg", { type: "image/jpeg" });
    dataTransfer.items.add(file);
    activeInput.files = dataTransfer.files;
  };

  const saveAdjustedPhoto = () => {
    if (!activeInput || !activeImage) {
      return;
    }

    canvas.toBlob((blob) => {
      if (!blob) {
        return;
      }
      setAdjustedFile(blob);
      const form = activeInput.closest("[data-profile-photo-form]");
      const autoSubmit = form && form.dataset.profilePhotoAutoSubmit === "true";
      closeModal();
      if (autoSubmit && form) {
        form.requestSubmit();
      }
    }, "image/jpeg", 0.9);
  };

  document.querySelectorAll("[data-profile-photo-input]").forEach((input) => {
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) {
        return;
      }
      if (!file.type.startsWith("image/")) {
        input.value = "";
        window.alert("Upload a valid image file.");
        return;
      }
      openModal(input, file);
    });
  });

  zoomInput.addEventListener("input", () => {
    state.zoom = Number(zoomInput.value);
    draw();
  });

  xInput.addEventListener("input", () => {
    state.offsetX = Number(xInput.value);
    draw();
  });

  yInput.addEventListener("input", () => {
    state.offsetY = Number(yInput.value);
    draw();
  });

  resetButton.addEventListener("click", () => {
    resetControls();
    draw();
  });

  saveButton.addEventListener("click", saveAdjustedPhoto);
  cancelButton.addEventListener("click", () => {
    if (activeInput) {
      activeInput.value = "";
    }
    closeModal();
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      if (activeInput) {
        activeInput.value = "";
      }
      closeModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) {
      if (activeInput) {
        activeInput.value = "";
      }
      closeModal();
    }
  });
})();
