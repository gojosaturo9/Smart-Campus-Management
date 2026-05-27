document.querySelectorAll("[data-live-face-scan]").forEach((scanner) => {
  const video = scanner.querySelector("[data-scan-video]");
  const canvas = scanner.querySelector("[data-scan-canvas]");
  const fileInput = scanner.querySelector("[data-face-photo]");
  const status = scanner.querySelector("[data-scan-status]");
  const frame = scanner.querySelector(".face-camera-frame");
  const form = scanner.closest("form");
  const submitButton = form.querySelector('button[type="submit"]');
  const scanOptional = scanner.dataset.scanOptional === "true";
  const processingStatus = scanner.dataset.processingStatus || "Processing...";
  let stream = null;
  let submitting = false;

  const setStatus = (message) => {
    status.textContent = message;
  };

  const setBusy = () => {
    scanner.classList.add("scanned");
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Processing...";
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
  };

  const startCamera = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Camera is not supported in this browser");
      return false;
    }

    try {
      stopCamera();
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 960 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      video.srcObject = stream;
      setStatus("Camera ready");
      return true;
    } catch (error) {
      setStatus("Camera permission required");
      return false;
    }
  };

  const setFile = (blob) => {
    const file = new File([blob], "live-face-scan.jpg", { type: "image/jpeg" });
    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
  };

  const waitForVideo = () =>
    new Promise((resolve) => {
      if (video.videoWidth && video.videoHeight) {
        resolve(true);
        return;
      }

      const timeout = window.setTimeout(() => resolve(false), 2500);
      video.addEventListener(
        "loadedmetadata",
        () => {
          window.clearTimeout(timeout);
          resolve(true);
        },
        { once: true },
      );
    });

  const captureFace = () =>
    new Promise((resolve) => {
      if (!video.videoWidth || !video.videoHeight) {
        setStatus("Camera is still loading");
        resolve(false);
        return;
      }

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext("2d");
      context.translate(canvas.width, 0);
      context.scale(-1, 1);
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      video.hidden = true;
      frame.classList.add("captured");
      frame.hidden = true;
      setStatus(processingStatus);

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            setStatus("Face capture failed");
            resolve(false);
            return;
          }
          setFile(blob);
          stopCamera();
          resolve(true);
        },
        "image/jpeg",
        0.92,
      );
    });

  form.addEventListener("submit", async (event) => {
    if (submitting) {
      return;
    }

    if (scanOptional && !stream && !fileInput.files.length) {
      submitting = true;
      setBusy();
      return;
    }

    event.preventDefault();
    setBusy();

    if (!stream && !(await startCamera())) {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = submitButton.dataset.originalText || submitButton.textContent;
      }
      return;
    }

    if (!(await waitForVideo())) {
      setStatus("Camera is still loading");
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = submitButton.dataset.originalText || submitButton.textContent;
      }
      return;
    }

    const captured = await captureFace();
    if (!captured) {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = submitButton.dataset.originalText || submitButton.textContent;
      }
      return;
    }

    submitting = true;
    form.submit();
  });

  if (submitButton) {
    submitButton.dataset.originalText = submitButton.textContent;
  }

  window.addEventListener("pagehide", stopCamera);

  if (!scanOptional) {
    startCamera();
  }
});
