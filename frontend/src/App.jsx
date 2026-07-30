import { useEffect, useMemo, useRef, useState } from "react";
import {
  NavLink,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";
import { authenticatedRequest } from "./services/authService";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import Register from "./pages/Register";
import Users from "./pages/Users";
import useAuth from "./hooks/useAuth";
import Login from "./pages/Login";
import Unauthorized from "./pages/Unauthorized";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const SCREENING_API =
  `${API_BASE_URL}/api/v1/screening/predict`;

const REPORT_API =
  `${API_BASE_URL}/api/v1/reports/generate`;

const PATIENTS_API =
  `${API_BASE_URL}/api/v1/patients`;

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const ALLOWED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/bmp",
];

function ScreeningPage() {
  const fileInputRef = useRef(null);
  const [searchParams] = useSearchParams();
  const existingPatientId = searchParams.get("patientId");
  const [darkMode, setDarkMode] = useState(() => {
    return (localStorage.getItem("oralvision-theme") || localStorage.getItem("oralscan-theme")) === "dark";
  });

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState(null);

  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisStep, setAnalysisStep] = useState("");
  const [error, setError] = useState("");

  const [gradcamOpacity, setGradcamOpacity] = useState(100);
  const [comparisonMode, setComparisonMode] = useState("side-by-side");

  const [patientDetails, setPatientDetails] = useState({
    name: "",
    age: "",
    gender: "",
    phone: "",
    patientId: "",
    referredBy: "",
    doctorName: "",
    hospitalName: "OralVision",
  });

  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState("");
  const [generatedReport, setGeneratedReport] = useState(null);
  const [patientSaving, setPatientSaving] = useState(false);
  const [patientSaved, setPatientSaved] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      darkMode ? "dark" : "light"
    );

    localStorage.setItem(
      "oralvision-theme",
      darkMode ? "dark" : "light"
    );
  }, [darkMode]);

  useEffect(() => {
    if (!existingPatientId) {
      return;
    }

    const loadExistingPatient = async () => {
      try {
        setPatientSaving(true);
        setError("");

        const patient = await authenticatedRequest(
          `/api/v1/patients/${existingPatientId}`
        );

        setPatientDetails({
          name: patient.patient_name || "",
          age: patient.age || "",
          gender: patient.gender || "",
          phone: patient.phone || "",
          patientId: patient.id || existingPatientId,
          referredBy: patient.referred_by || "",
          doctorName: patient.doctor_name || "",
          hospitalName:
            patient.hospital_name || "OralVision",
        });

        setPatientSaved(true);
      } catch (requestError) {
        setError(
          requestError.message ||
          "Unable to load the selected patient."
        );
      } finally {
        setPatientSaving(false);
      }
    };

    loadExistingPatient();
  }, [existingPatientId]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const gradcamUrl = useMemo(() => {
    if (!result?.gradcam?.url) {
      return "";
    }

    return `${API_BASE_URL}${result.gradcam.url}`;
  }, [result]);

  const reportDownloadUrl = useMemo(() => {
    if (!generatedReport?.download_url) {
      return "";
    }

    return `${API_BASE_URL}${generatedReport.download_url}`;
  }, [generatedReport]);

  const isCancerPrediction = useMemo(() => {
    if (!result?.prediction) {
      return false;
    }

    const normalized = result.prediction
      .toUpperCase()
      .replaceAll("_", " ");

    return (
      normalized.includes("CANCER") &&
      !normalized.includes("NON")
    );
  }, [result]);

  const patientValidation = useMemo(() => {
    const errors = {};
    const name = patientDetails.name.trim();
    const age = Number(patientDetails.age);
    const phone = patientDetails.phone.replace(/\D/g, "");

    if (name.length < 2) {
      errors.name = "Enter at least 2 characters.";
    }

    if (!patientDetails.age || age < 1 || age > 120) {
      errors.age = "Age must be between 1 and 120.";
    }

    if (!patientDetails.gender) {
      errors.gender = "Select a gender.";
    }

    if (phone.length < 10 || phone.length > 15) {
      errors.phone = "Phone must contain 10 to 15 digits.";
    }

    return {
      errors,
      isValid: Object.keys(errors).length === 0,
    };
  }, [patientDetails]);

  function clinicalPredictionLabel(prediction) {
    const normalized = prediction?.toUpperCase().replaceAll("_", " ") || "";

    if (normalized.includes("NON CANCER")) {
      return "No suspicious lesion detected";
    }

    if (normalized.includes("CANCER")) {
      return "Suspicious lesion detected";
    }

    return normalized || "Screening result";
  }

  async function ensurePatientRecord() {
    if (existingPatientId) {
      return existingPatientId;
    }

    if (patientSaved && patientDetails.patientId) {
      return patientDetails.patientId;
    }

    setFieldErrors(patientValidation.errors);

    if (!patientValidation.isValid) {
      throw new Error(
        "Please correct the patient details before screening."
      );
    }

    setPatientSaving(true);

    try {
      const data = await authenticatedRequest(
        "/api/v1/patients",
        {
          method: "POST",
          body: JSON.stringify({
            patient_name:
              patientDetails.name.trim(),
            age: Number(patientDetails.age),
            gender: patientDetails.gender,
            phone:
              patientDetails.phone.replace(/\D/g, ""),
            email: null,
            referred_by:
              patientDetails.referredBy.trim() ||
              null,
            doctor_name:
              patientDetails.doctorName.trim() ||
              null,
            hospital_name:
              patientDetails.hospitalName.trim() ||
              "OralVision",
          }),
        }
      );

      setPatientDetails((current) => ({
        ...current,
        patientId: data.id,
      }));

      setPatientSaved(true);

      return data.id;
    } finally {
      setPatientSaving(false);
    }
  }

  function handlePatientChange(event) {
    const { name, value } = event.target;

    setPatientDetails((current) => ({
      ...current,
      [name]: value,
    }));

    setGeneratedReport(null);
    setReportError("");

    if (name !== "patientId") {
      setPatientSaved(false);
    }

    setFieldErrors((current) => ({
      ...current,
      [name]: "",
    }));
  }

  function validateFile(file) {
    if (!file) {
      return false;
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
      setError(
        "Unsupported image format. Upload JPG, PNG, WEBP, or BMP."
      );
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("The selected image must be smaller than 10 MB.");
      return false;
    }

    return true;
  }

  function selectFile(file) {
    setError("");
    setResult(null);

    if (!validateFile(file)) {
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setUploadProgress(0);
  }

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    selectFile(file);
  }

  function handleDragOver(event) {
    event.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(event) {
    event.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];
    selectFile(file);
  }

  function simulateProgress() {
    setUploadProgress(8);
    setAnalysisStep("Uploading image securely...");

    const intervals = [
      {
        delay: 350,
        progress: 28,
        message: "Checking image quality...",
      },
      {
        delay: 850,
        progress: 52,
        message: "Running EfficientNet analysis...",
      },
      {
        delay: 1450,
        progress: 73,
        message: "Calculating confidence scores...",
      },
      {
        delay: 2100,
        progress: 88,
        message: "Generating Grad-CAM explanation...",
      },
    ];

    return intervals.map(({ delay, progress, message }) =>
      window.setTimeout(() => {
        setUploadProgress(progress);
        setAnalysisStep(message);
      }, delay)
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setFieldErrors(patientValidation.errors);

    if (!patientValidation.isValid) {
      setError("Please complete the required patient details correctly.");
      return;
    }

    if (!selectedFile) {
      setError("Please upload an oral image before screening.");
      return;
    }

    setLoading(true);
    setResult(null);
    setError("");

    const timers = simulateProgress();

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const patientId = await ensurePatientRecord();
      formData.append("patient_id", patientId);

      const data = await authenticatedRequest(
        "/api/v1/screening/predict",
        {
          method: "POST",
          body: formData,
        }
      );

      setUploadProgress(100);
      setAnalysisStep("Analysis complete.");

      window.setTimeout(() => {
        setResult(data);
        setLoading(false);
      }, 450);
    } catch (requestError) {
      setLoading(false);
      setUploadProgress(0);
      setAnalysisStep("");

      setError(
        requestError.message ||
        "Unable to connect to the OralVision backend."
      );
    } finally {
      timers.forEach((timer) => clearTimeout(timer));
    }
  }

  async function generatePdfReport() {
    if (!result || !selectedFile) {
      setReportError(
        "Run the AI screening before generating a report."
      );
      return;
    }

    if (!patientValidation.isValid) {
      setFieldErrors(patientValidation.errors);
      setReportError("Complete valid patient details before generating the report.");
      return;
    }

    setReportLoading(true);
    setReportError("");

    const formData = new FormData();

    let patientId;

    try {
      patientId = await ensurePatientRecord();
    } catch (patientError) {
      setReportLoading(false);
      setReportError(patientError.message);
      return;
    }

    formData.append("file", selectedFile);
    formData.append(
      "screening_result",
      JSON.stringify(result)
    );

    formData.append("patient_name", patientDetails.name);
    formData.append("patient_age", patientDetails.age);
    formData.append("patient_gender", patientDetails.gender);
    formData.append("patient_phone", patientDetails.phone);
    formData.append("patient_id", patientId);
    formData.append("referred_by", patientDetails.referredBy);
    formData.append("doctor_name", patientDetails.doctorName);
    formData.append(
      "hospital_name",
      patientDetails.hospitalName
    );

    try {
      const data = await authenticatedRequest(
        "/api/v1/reports/generate",
        {
          method: "POST",
          body: formData,
        }
      );

      setGeneratedReport(data);

      window.open(
        `${API_BASE_URL}${data.download_url}`,
        "_blank",
        "noopener,noreferrer"
      );
    } catch (requestError) {
      setReportError(
        requestError.message ||
        "PDF report generation failed."
      );
    } finally {
      setReportLoading(false);
    }
  }

  function clearScreening() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(null);
    setPreviewUrl("");
    setResult(null);
    setError("");
    setUploadProgress(0);
    setAnalysisStep("");
    setGradcamOpacity(100);
    setGeneratedReport(null);
    setReportError("");
    setReportLoading(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function scrollToScreening() {
    document
      .getElementById("screening")
      ?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-container">
          <a href="#home" className="brand">
            <div className="brand-icon"><img src="/oralvision-logo.svg" alt="OralVision logo" /></div>

            <div>
              <strong>OralVision</strong>
              <span>Explainable AI screening support</span>
            </div>
          </a>

          <div className="nav-links">
            <a href="#home">Home</a>
            <a href="#screening">Screening</a>
            <a href="#about">How it works</a>
          </div>

          <button
            type="button"
            className="theme-toggle"
            onClick={() => setDarkMode((current) => !current)}
            aria-label="Toggle dark mode"
          >
            <span>{darkMode ? "☀" : "☾"}</span>
            <small>{darkMode ? "Light" : "Dark"}</small>
          </button>
        </div>
      </nav>

      <main>
        <section id="home" className="hero-section">
          <div className="hero-background hero-background-one" />
          <div className="hero-background hero-background-two" />

          <div className="hero-container">
            <div className="hero-content">
              <div className="hero-badge">
                <span className="status-dot" />
                AI-assisted preliminary screening
              </div>

              <h1>
                Smarter oral health screening with
                <span> explainable AI.</span>
              </h1>

              <p>
                OralVision analyzes oral cavity images using
                EfficientNet-B0, evaluates image quality, and
                generates Grad-CAM visual explanations to support
                preliminary screening.
              </p>

              <div className="hero-actions">
                <button
                  type="button"
                  className="primary-hero-button"
                  onClick={scrollToScreening}
                >
                  Start screening
                  <span>→</span>
                </button>

                <a href="#about" className="secondary-hero-button">
                  Learn how it works
                </a>
              </div>

              <div className="hero-highlights">
                <div>
                  <strong>87.10%</strong>
                  <span>Test accuracy</span>
                </div>

                <div>
                  <strong>0.9292</strong>
                  <span>ROC-AUC score</span>
                </div>

                <div>
                  <strong>Grad-CAM</strong>
                  <span>Visual explanation</span>
                </div>
              </div>
            </div>

            <div className="hero-visual glass-card">
              <div className="visual-header">
                <div>
                  <span className="visual-label">
                    Screening preview
                  </span>
                  <h3>AI analysis dashboard</h3>
                </div>

                <div className="live-indicator">
                  <span />
                  Ready
                </div>
              </div>

              <div className="visual-image">
                <div className="scan-ring scan-ring-one" />
                <div className="scan-ring scan-ring-two" />

                <div className="medical-symbol">+</div>
              </div>

              <div className="visual-stats">
                <div>
                  <span>Model</span>
                  <strong>EfficientNet-B0</strong>
                </div>

                <div>
                  <span>Explainability</span>
                  <strong>Grad-CAM</strong>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="screening" className="screening-section">
          <div className="section-title">
            <span>AI screening workspace</span>
            <h2>Upload and analyze an oral image</h2>
            <p>
              Use a clear, focused, and well-lit image of the oral
              region for better screening quality.
            </p>
          </div>

          <div className="screening-layout">
            <form
              className="upload-card glass-card"
              onSubmit={handleSubmit}
            >
              <div className="card-heading">
                <div className="step-number">01</div>

                <div>
                  <h3>Upload image</h3>
                  <p>Drag and drop or browse from your device.</p>
                </div>
              </div>

              <div className="patient-form">
                <div className="patient-form-header">
                  <div>
                    <span>Patient information</span>
                    <h4>Details for the screening report</h4>
                  </div>

                  <small>{patientSaved ? "✓ Patient saved" : "* Required fields"}</small>
                </div>

                <div className="patient-form-grid">
                  <label className="full-width">
                    <span className="field-label">Patient name <span className="required-mark">*</span>{patientDetails.name.trim().length >= 2 && <span className="valid-mark">✓</span>}</span>
                    <input
                      type="text"
                      name="name"
                      value={patientDetails.name}
                      onChange={handlePatientChange}
                      placeholder="Enter patient name"
                      required
                      aria-invalid={Boolean(existingPatientId ? false : Boolean(fieldErrors.name))}
                    />
                    {fieldErrors.name && <em className="field-error">{fieldErrors.name}</em>}
                  </label>

                  <label>
                    <span className="field-label">Age <span className="required-mark">*</span>{patientDetails.age && Number(patientDetails.age) >= 1 && Number(patientDetails.age) <= 120 && <span className="valid-mark">✓</span>}</span>
                    <input
                      type="number"
                      name="age"
                      min="1"
                      max="120"
                      value={patientDetails.age}
                      onChange={handlePatientChange}
                      placeholder="Age"
                      required
                      aria-invalid={Boolean(existingPatientId ? false : Boolean(fieldErrors.age))}
                    />
                    {fieldErrors.age && <em className="field-error">{fieldErrors.age}</em>}
                  </label>

                  <label>
                    <span className="field-label">Gender <span className="required-mark">*</span>{patientDetails.gender && <span className="valid-mark">✓</span>}</span>
                    <select
                      name="gender"
                      value={patientDetails.gender}
                      onChange={handlePatientChange}
                      required
                      aria-invalid={Boolean(fieldErrors.gender)}
                    >
                      <option value="">Select gender</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                    {fieldErrors.gender && <em className="field-error">{fieldErrors.gender}</em>}
                  </label>

                  <label>
                    <span className="field-label">Phone <span className="required-mark">*</span>{patientDetails.phone.replace(/\D/g, "").length >= 10 && patientDetails.phone.replace(/\D/g, "").length <= 15 && <span className="valid-mark">✓</span>}</span>
                    <input
                      type="tel"
                      name="phone"
                      value={patientDetails.phone}
                      onChange={handlePatientChange}
                      placeholder="Phone number"
                      required
                      inputMode="numeric"
                      maxLength={15}
                      aria-invalid={Boolean(fieldErrors.phone)}
                    />
                    {fieldErrors.phone && <em className="field-error">{fieldErrors.phone}</em>}
                  </label>

                  <label>
                    <span className="field-label">Patient ID <span className="auto-label">Auto-generated</span></span>
                    <input
                      type="text"
                      name="patientId"
                      value={patientDetails.patientId}
                      readOnly
                      placeholder="Auto-generated"
                    />
                  </label>

                  <label>
                    <span className="field-label">Referred by <span className="optional-label">Optional</span></span>
                    <input
                      type="text"
                      name="referredBy"
                      value={patientDetails.referredBy}
                      onChange={handlePatientChange}
                      placeholder="Referring doctor"
                    />
                  </label>

                  <label>
                    <span className="field-label">Doctor name <span className="optional-label">Optional</span></span>
                    <input
                      type="text"
                      name="doctorName"
                      value={patientDetails.doctorName}
                      onChange={handlePatientChange}
                      placeholder="Reviewing doctor"
                    />
                  </label>

                  <label className="full-width">
                    <span className="field-label">Hospital / Project name <span className="optional-label">Optional</span></span>
                    <input
                      type="text"
                      name="hospitalName"
                      value={patientDetails.hospitalName}
                      readOnly
                      placeholder="OralVision"
                    />
                  </label>
                </div>
              </div>

              <div
                className={`drop-zone ${isDragging ? "drop-zone-active" : ""
                  } ${previewUrl ? "drop-zone-preview" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" ||
                    event.key === " "
                  ) {
                    fileInputRef.current?.click();
                  }
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".jpg,.jpeg,.png,.webp,.bmp"
                  onChange={handleFileChange}
                  hidden
                />

                {previewUrl ? (
                  <div className="preview-wrapper">
                    <img
                      src={previewUrl}
                      alt="Selected oral scan"
                    />

                    <div className="preview-overlay">
                      <span>Click to replace image</span>
                    </div>
                  </div>
                ) : (
                  <div className="drop-content">
                    <div className="upload-symbol">↑</div>

                    <h4>
                      {isDragging
                        ? "Drop the image here"
                        : "Drag and drop an oral image"}
                    </h4>

                    <p>or click to browse your files</p>

                    <div className="file-support">
                      JPG, PNG, WEBP, BMP · Max 10 MB
                    </div>
                  </div>
                )}
              </div>

              {selectedFile && (
                <div className="selected-file">
                  <div className="file-icon">IMG</div>

                  <div className="file-information">
                    <strong>{selectedFile.name}</strong>
                    <span>
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={clearScreening}
                    aria-label="Remove selected image"
                  >
                    ×
                  </button>
                </div>
              )}

              {loading && (
                <div className="progress-card">
                  <div className="progress-information">
                    <span>{analysisStep}</span>
                    <strong>{uploadProgress}%</strong>
                  </div>

                  <div className="progress-bar">
                    <div
                      className="progress-value"
                      style={{
                        width: `${uploadProgress}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {error && (
                <div className="error-alert">
                  <span>!</span>
                  <p>{error}</p>
                </div>
              )}

              <div className="upload-actions">
                <button
                  type="submit"
                  className="screen-button"
                  disabled={
                    loading ||
                    patientSaving ||
                    !selectedFile ||
                    !patientValidation.isValid
                  }
                >
                  {loading || patientSaving ? (
                    <>
                      <span className="button-spinner" />
                      {patientSaving ? "Saving patient" : "Analyzing image"}
                    </>
                  ) : (
                    <>
                      Run AI screening
                      <span>→</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  className="clear-button"
                  onClick={clearScreening}
                  disabled={loading}
                >
                  Clear
                </button>
              </div>

              <div className="privacy-note">
                <span>✓</span>
                Images are processed only for screening analysis.
              </div>
            </form>

            <section className="result-card glass-card">
              <div className="card-heading">
                <div className="step-number">02</div>

                <div>
                  <h3>Screening result</h3>
                  <p>
                    Review prediction, confidence, quality, and
                    Grad-CAM.
                  </p>
                </div>
              </div>

              {!loading && !result && (
                <div className="empty-result">
                  <div className="empty-result-graphic">
                    <div className="empty-circle empty-circle-one" />
                    <div className="empty-circle empty-circle-two" />
                    <span>AI</span>
                  </div>

                  <h4>No analysis available</h4>
                  <p>
                    Upload an oral image and run the AI screening
                    to view the result.
                  </p>
                </div>
              )}

              {loading && (
                <div className="analysis-loader">
                  <div className="analysis-animation">
                    <span />
                    <span />
                    <span />
                  </div>

                  <h4>Analyzing oral image</h4>
                  <p>{analysisStep}</p>
                </div>
              )}

              {result && (
                <div className="result-content">
                  <div
                    className={`prediction-card ${isCancerPrediction
                      ? "prediction-cancer"
                      : "prediction-non-cancer"
                      }`}
                  >
                    <div>
                      <span className="prediction-label">
                        AI prediction
                      </span>

                      <h3>
                        {clinicalPredictionLabel(result.prediction)}
                      </h3>

                      <p>{result.message}</p>
                    </div>

                    <div className="confidence-display">
                      <div
                        className="confidence-ring"
                        style={{
                          "--confidence":
                            `${result.confidence_percent * 3.6}deg`,
                        }}
                      >
                        <div>
                          <strong>
                            {result.confidence_percent}%
                          </strong>
                          <span>AI confidence</span>
                        </div>
                      </div>

                      <span
                        className={`confidence-badge confidence-${result.confidence_level}`}
                      >
                        {result.confidence_level}
                      </span>
                    </div>
                  </div>

                  <div className="result-information-grid">
                    <article className="information-card">
                      <div className="information-header">
                        <h4>Class probabilities</h4>
                        <span>Model output</span>
                      </div>

                      <div className="probability-list">
                        {Object.entries(
                          result.probabilities
                        ).map(([label, value]) => (
                          <div
                            className="probability-item"
                            key={label}
                          >
                            <div>
                              <span>
                                {label.replaceAll("_", " ")}
                              </span>
                              <strong>
                                {(value * 100).toFixed(2)}%
                              </strong>
                            </div>

                            <div className="probability-track">
                              <div
                                className="probability-value"
                                style={{
                                  width: `${value * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </article>

                    <article className="information-card">
                      <div className="information-header">
                        <h4>Image quality</h4>

                        <span
                          className={`quality-status quality-${result.image_quality.status}`}
                        >
                          {result.image_quality.status}
                        </span>
                      </div>

                      <div className="quality-stats">
                        <div>
                          <span>Resolution</span>
                          <strong>
                            {result.image_quality.width} ×{" "}
                            {result.image_quality.height}
                          </strong>
                        </div>

                        <div>
                          <span>Blur score</span>
                          <strong>
                            {result.image_quality.blur_score}
                          </strong>
                        </div>
                      </div>

                      {result.image_quality.issues.length > 0 ? (
                        <div className="quality-issues">
                          {result.image_quality.issues.map(
                            (issue) => (
                              <div key={issue}>
                                <span>!</span>
                                <p>{issue}</p>
                              </div>
                            )
                          )}
                        </div>
                      ) : (
                        <div className="quality-success">
                          <span>✓</span>
                          Image quality is suitable for screening.
                        </div>
                      )}
                    </article>
                  </div>

                  <article className="gradcam-viewer">
                    <div className="gradcam-header">
                      <div>
                        <span>Visual explanation</span>
                        <h4>Grad-CAM attention map</h4>
                        <p>
                          Highlighted areas show regions that most
                          influenced the prediction.
                        </p>
                      </div>

                      <div className="viewer-controls">
                        <button
                          type="button"
                          className={
                            comparisonMode === "side-by-side"
                              ? "active"
                              : ""
                          }
                          onClick={() =>
                            setComparisonMode("side-by-side")
                          }
                        >
                          Compare
                        </button>

                        <button
                          type="button"
                          className={
                            comparisonMode === "overlay"
                              ? "active"
                              : ""
                          }
                          onClick={() =>
                            setComparisonMode("overlay")
                          }
                        >
                          Overlay
                        </button>
                      </div>
                    </div>

                    {comparisonMode === "side-by-side" ? (
                      <div className="comparison-grid">
                        <figure>
                          <div className="image-label">
                            Original image
                          </div>

                          <img
                            src={previewUrl}
                            alt="Original oral scan"
                          />
                        </figure>

                        <figure>
                          <div className="image-label">
                            Grad-CAM result
                          </div>

                          <img
                            src={gradcamUrl}
                            alt="Grad-CAM visualization"
                          />
                        </figure>
                      </div>
                    ) : (
                      <div className="overlay-viewer">
                        <img
                          src={previewUrl}
                          alt="Original oral scan"
                          className="overlay-original"
                        />

                        <img
                          src={gradcamUrl}
                          alt="Grad-CAM overlay"
                          className="overlay-gradcam"
                          style={{
                            opacity: gradcamOpacity / 100,
                          }}
                        />
                      </div>
                    )}

                    <div className="opacity-control">
                      <label htmlFor="opacity">
                        Heatmap visibility
                      </label>

                      <input
                        id="opacity"
                        type="range"
                        min="0"
                        max="100"
                        value={gradcamOpacity}
                        onChange={(event) =>
                          setGradcamOpacity(
                            Number(event.target.value)
                          )
                        }
                        disabled={
                          comparisonMode !== "overlay"
                        }
                      />

                      <strong>{gradcamOpacity}%</strong>
                    </div>
                  </article>

                  <div className="medical-disclaimer">
                    <div className="disclaimer-icon">i</div>

                    <div>
                      <strong>Medical disclaimer</strong>
                      <p>{result.disclaimer}</p>
                    </div>
                  </div>
                  <div className="report-actions-card">
                    <div className="report-actions-content">
                      <div className="report-document-icon">PDF</div>

                      <div>
                        <h4>Professional screening report</h4>
                        <p>
                          Generate a PDF containing the patient details,
                          uploaded image, Grad-CAM result, prediction,
                          confidence, QR verification, and signature fields.
                        </p>
                      </div>
                    </div>

                    {reportError && (
                      <div className="report-error">
                        {reportError}
                      </div>
                    )}

                    <div className="report-button-row">
                      <button
                        type="button"
                        className="generate-report-button"
                        onClick={generatePdfReport}
                        disabled={reportLoading}
                      >
                        {reportLoading ? (
                          <>
                            <span className="button-spinner" />
                            Generating report...
                          </>
                        ) : (
                          <>
                            Download screening report
                            <span>↓</span>
                          </>
                        )}
                      </button>

                      {reportDownloadUrl && (
                        <a
                          href={reportDownloadUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="open-report-button"
                        >
                          Open report
                        </a>
                      )}
                    </div>

                    {generatedReport && (
                      <div className="generated-report-details">
                        <span>
                          Report ID
                          <strong>{generatedReport.report_id}</strong>
                        </span>

                        <span>
                          Status
                          <strong>Generated successfully</strong>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </section>
          </div>
        </section>

        <section id="about" className="how-it-works">
          <div className="section-title">
            <span>Screening process</span>
            <h2>How OralVision works</h2>
            <p>
              The system combines image validation, deep learning,
              and explainable AI in a simple workflow.
            </p>
          </div>

          <div className="process-grid">
            <article className="process-card glass-card">
              <div className="process-icon">01</div>
              <h3>Upload</h3>
              <p>
                A clear oral cavity image is securely submitted
                through the screening interface.
              </p>
            </article>

            <article className="process-card glass-card">
              <div className="process-icon">02</div>
              <h3>Analyze</h3>
              <p>
                EfficientNet-B0 evaluates the image and calculates
                class probabilities.
              </p>
            </article>

            <article className="process-card glass-card">
              <div className="process-icon">03</div>
              <h3>Explain</h3>
              <p>
                Grad-CAM highlights the image regions that most
                influenced the AI result.
              </p>
            </article>

            <article className="process-card glass-card">
              <div className="process-icon">04</div>
              <h3>Consult</h3>
              <p>
                Users are advised to seek professional clinical
                examination when required.
              </p>
            </article>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="footer-container">
          <div className="footer-brand">
            <div className="brand-icon"><img src="/oralvision-logo.svg" alt="OralVision logo" /></div>

            <div>
              <strong>OralVision</strong>
              <p>
                Explainable AI for preliminary oral cancer screening.
              </p>
            </div>
          </div>

          <div className="footer-disclaimer">
            This application is intended for academic and
            preliminary screening support only. It is not a
            substitute for professional medical diagnosis.
          </div>

          <div className="footer-bottom">
            <span>© 2026 OralVision · Version 1.0</span>
            <span>B.Tech CSE Major Project</span>
          </div>
        </div>
      </footer>
    </div>
  );
}


const formatDate = (value) => {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
};

async function apiRequest(path, options = {}) {
  return authenticatedRequest(path, options);
}


function Shell({ darkMode, setDarkMode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    setMobileMenuOpen(false);
    navigate("/login", { replace: true });
  };


  useEffect(() => {
    const closeMenuOnResize = () => {
      if (window.innerWidth > 1100) {
        setMobileMenuOpen(false);
      }
    };

    window.addEventListener("resize", closeMenuOnResize);
    return () =>
      window.removeEventListener("resize", closeMenuOnResize);
  }, []);

  useEffect(() => {
    document.body.style.overflow =
      mobileMenuOpen ? "hidden" : "";

    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  return (
    <div className="emr-shell">
      <header className="emr-mobile-header">
        <button
          type="button"
          className="emr-menu-button"
          onClick={() =>
            setMobileMenuOpen((current) => !current)
          }
          aria-label="Toggle navigation menu"
          aria-expanded={mobileMenuOpen}
        >
          <span />
          <span />
          <span />
        </button>

        <div className="emr-mobile-brand">
          <div className="brand-icon">
            <img
              src="/oralvision-logo.svg"
              alt="OralVision logo"
            />
          </div>

          <div>
            <strong>OralVision</strong>
            <span>AI-powered screening</span>
          </div>
        </div>

        <button
          type="button"
          className="emr-mobile-theme"
          onClick={() =>
            setDarkMode((value) => !value)
          }
          aria-label="Toggle color theme"
        >
          {darkMode ? "☀" : "☾"}
        </button>
      </header>

      {mobileMenuOpen && (
        <button
          type="button"
          className="emr-sidebar-backdrop"
          onClick={() => setMobileMenuOpen(false)}
          aria-label="Close navigation menu"
        />
      )}

      <Sidebar
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        mobileMenuOpen={mobileMenuOpen}
        setMobileMenuOpen={setMobileMenuOpen}
        onLogout={handleLogout}
      />

      <main className="emr-main">
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "doctor",
                  "technician",
                ]}
              >
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/screening"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "doctor",
                  "technician",
                ]}
              >
                <ScreeningPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "doctor",
                ]}
              >
                <PatientsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:patientId"
            element={<PatientDetailPage />}
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "doctor",
                ]}
              >
                <ReportsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/search"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "doctor",
                ]}
              >
                <SearchPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/statistics"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "doctor",
                ]}
              >
                <StatisticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                  "doctor",
                ]}
              >
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <Users />
              </ProtectedRoute>
            }
          />

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/register"
            element={<Register />}
          />
          <Route
            path="/unauthorized"
            element={<Unauthorized />}
          />
        </Routes>
      </main>
    </div>
  );
}

function PageHeader({ eyebrow, title, description, action }) {
  return (
    <header className="emr-page-header">
      <div><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>
      {action}
    </header>
  );
}

function LoadingState({ label = "Loading patient records..." }) {
  return <div className="emr-state"><span className="button-spinner" />{label}</div>;
}

function ErrorState({ message, onRetry }) {
  return <div className="emr-state emr-error">
    <strong>
      Unable to retrieve data.
      Please ensure the backend server is running.
    </strong>
    <p>{message}</p>
    {onRetry && <button onClick={onRetry}>Retry</button>}
  </div>;
}

function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const load = async () => {
    try { setError(""); setStats(await apiRequest("/api/v1/dashboard/stats")); }
    catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, []);
  if (error) return <div className="emr-page"><ErrorState message={error} onRetry={load} /></div>;
  if (!stats) return <div className="emr-page"><LoadingState label="Loading dashboard..." /></div>;

  const summary = stats.summary || {};
  const cards = [
    ["Total patients", summary.total_patients ?? 0, "Registered records"],
    ["Total screenings", summary.total_screenings ?? 0, "AI analyses completed"],
    ["Total reports", summary.total_reports ?? 0, "PDF reports generated"],
    ["Suspicious cases", summary.suspicious_cases ?? 0, "Require clinical review"],
    ["Non-cancer cases", summary.non_cancer_cases ?? 0, "Low-risk screenings"],
  ];
  const recent = stats.recent_patients || [];
  return (
    <div className="emr-page">
      <PageHeader eyebrow="Overview" title="Clinical dashboard" description="A live summary of patients, screenings, reports, and model outcomes." action={<button className="emr-primary" onClick={() => navigate('/screening')}>+ New screening</button>} />
      <section className="emr-stat-grid">{cards.map(([label, value, note]) => <article key={label} className="emr-stat-card"><span>{label}</span><strong>{value}</strong><small>{note}</small></article>)}</section>
      <section className="emr-two-column">
        <article className="emr-panel"><div className="emr-panel-title"><h2>Recent patients</h2><button onClick={() => navigate('/patients')}>View all</button></div>{recent.length ? <div className="emr-list">{recent.map((p) => <button key={p.id} onClick={() => navigate(`/patients/${p.id}`)}><span className="avatar">{(p.patient_name || 'P')[0]}</span><span><strong>{p.patient_name}</strong><small>{p.phone || 'No phone'} · {p.gender || '—'}</small></span><time>{formatDate(p.created_at)}</time></button>)}</div> : <p className="emr-muted">No recent patients yet.</p>}</article>
        <article className="emr-panel"><div className="emr-panel-title"><h2>Quick actions</h2></div><div className="quick-actions"><button onClick={() => navigate('/screening')}><b>+</b><span>Start screening<small>Create patient and analyze image</small></span></button><button onClick={() => navigate('/patients')}><b>♙</b><span>Patient records<small>View and manage EMR data</small></span></button><button onClick={() => navigate('/reports')}><b>▤</b><span>Reports<small>Find generated PDFs</small></span></button><button onClick={() => navigate('/search')}><b>⌕</b><span>Global search<small>Search patients and screenings</small></span></button></div></article>
      </section>
    </div>
  );
}

function PatientsPage() {
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const load = async () => {
    try { setLoading(true); setError(""); const q = search.trim() ? `?search=${encodeURIComponent(search.trim())}&limit=200` : '?limit=200'; setPatients(await apiRequest(`/api/v1/patients${q}`)); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const removePatient = async (id, name) => {
    if (!window.confirm(`Delete patient ${name}?`)) return;
    try { await apiRequest(`/api/v1/patients/${id}`, { method: 'DELETE' }); setPatients((items) => items.filter((p) => p.id !== id)); }
    catch (e) { setError(e.message); }
  };
  return <div className="emr-page">
    <PageHeader eyebrow="EMR" title="Patients" description="Manage registered patients and open their screening history." action={<button className="emr-primary" onClick={() => navigate('/screening')}>+ Add patient</button>} />
    <div className="emr-toolbar"><input value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && load()} placeholder="Search by name, phone, or email" /><button onClick={load}>Search</button></div>
    {loading ? <LoadingState label="Loading patients..." /> : error ? <ErrorState message={error} onRetry={load} /> : <div className="emr-table-wrap"><table className="emr-table"><thead><tr><th>Patient</th><th>Age</th><th>Gender</th><th>Phone</th><th>Screenings</th><th>Reports</th><th>Actions</th></tr></thead><tbody>{patients.map((p) => <tr key={p.id}><td><div className="patient-cell"><span className="avatar">{(p.patient_name || 'P')[0]}</span><span><strong>{p.patient_name}</strong><small>{p.id}</small></span></div></td><td>{p.age ?? '—'}</td><td>{p.gender || '—'}</td><td>{p.phone || '—'}</td><td>{p.total_screenings ?? 0}</td><td>{p.total_reports ?? 0}</td><td><div className="row-actions">
      <button
        onClick={() =>
          navigate(`/patients/${p.id}`)
        }
      >
        View
      </button>

      <button
        onClick={() =>
          navigate(
            `/screening?patientId=${p.id}`
          )
        }
      >
        Screen
      </button>

      <button
        className="danger"
        onClick={() =>
          removePatient(p.id, p.patient_name)
        }
      >
        Delete
      </button>
    </div></td></tr>)}</tbody></table>{!patients.length && <div className="emr-empty">No patients found.</div>}</div>}
  </div>;
}

function PatientDetailPage() {
  const { patientId } = useParams();

  const [patient, setPatient] = useState(null);
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  const load = async () => {
    try {
      setLoading(true);
      setError("");

      const [patientData, historyData] = await Promise.all([
        apiRequest(`/api/v1/patients/${patientId}`),
        apiRequest(`/api/v1/patients/${patientId}/history`),
      ]);

      console.log("Patient data:", patientData);
      console.log("Patient history:", historyData);

      setPatient(patientData);
      setHistory(historyData);
    } catch (requestError) {
      console.error(
        "Patient history loading error:",
        requestError
      );

      setError(
        requestError.message ||
        "Unable to load the patient record."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [patientId]);

  if (loading) {
    return (
      <div className="emr-page">
        <LoadingState label="Loading patient record..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="emr-page">
        <ErrorState
          message={error}
          onRetry={load}
        />
      </div>
    );
  }

  if (!patient || !history) {
    return (
      <div className="emr-page">
        <ErrorState
          message="Patient record or history was not found."
          onRetry={load}
        />
      </div>
    );
  }

  const screenings =
    history.screenings ||
    history.screening_history ||
    [];

  const reports =
    history.reports ||
    [];

  const suspiciousCount = screenings.filter((screening) => {
    const prediction = String(
      screening.prediction || ""
    ).toLowerCase();

    return (
      (
        prediction.includes("cancer") ||
        prediction.includes("suspicious") ||
        prediction.includes("precancer")
      ) &&
      !prediction.includes("non")
    );
  }).length;

  const totalScreenings =
    history.total_screenings ??
    patient.total_screenings ??
    screenings.length;

  const totalReports =
    history.total_reports ??
    patient.total_reports ??
    reports.length;

  const formatConfidence = (record) => {
    if (
      record.confidence_percent !== undefined &&
      record.confidence_percent !== null
    ) {
      const value = Number(record.confidence_percent);

      return Number.isNaN(value)
        ? String(record.confidence_percent)
        : `${value.toFixed(2)}%`;
    }

    if (
      record.confidence !== undefined &&
      record.confidence !== null
    ) {
      const value = Number(record.confidence);

      if (Number.isNaN(value)) {
        return String(record.confidence);
      }

      return `${(value * 100).toFixed(2)}%`;
    }

    return "—";
  };

  const getDownloadUrl = (record) => {
    const url =
      record.report_download_url ||
      record.download_url;

    if (!url) {
      return "";
    }

    if (
      url.startsWith("http://") ||
      url.startsWith("https://")
    ) {
      return url;
    }

    return `${API_BASE_URL}${url}`;
  };

  return (
    <div className="emr-page">
      <PageHeader
        eyebrow="Patient record"
        title={patient.patient_name}
        description={`Patient ID: ${patient.id}`}
        action={
          <button
            type="button"
            className="emr-secondary"
            onClick={() => navigate("/patients")}
          >
            ← Back
          </button>
        }
      />

      <section className="patient-profile-grid">
        <article className="emr-panel patient-profile">
          <div className="patient-hero">
            <span className="avatar large">
              {patient.patient_name?.[0]?.toUpperCase() || "P"}
            </span>

            <div>
              <h2>{patient.patient_name}</h2>

              <p>
                {patient.gender || "—"} ·{" "}
                {patient.age ?? "—"} years
              </p>
            </div>
          </div>

          <dl>
            <div>
              <dt>Phone</dt>
              <dd>{patient.phone || "—"}</dd>
            </div>

            <div>
              <dt>Email</dt>
              <dd>{patient.email || "—"}</dd>
            </div>

            <div>
              <dt>Referred by</dt>
              <dd>{patient.referred_by || "—"}</dd>
            </div>

            <div>
              <dt>Doctor</dt>
              <dd>{patient.doctor_name || "—"}</dd>
            </div>

            <div>
              <dt>Hospital</dt>
              <dd>{patient.hospital_name || "—"}</dd>
            </div>

            <div>
              <dt>Created</dt>
              <dd>{formatDate(patient.created_at)}</dd>
            </div>
          </dl>

          <button
            type="button"
            className="emr-primary wide"
            onClick={() =>
              navigate(`/screening?patientId=${patient.id}`)
            }
          >
            Start new screening
          </button>
        </article>

        <article className="emr-panel">
          <div className="emr-panel-title">
            <h2>Record summary</h2>
          </div>

          <div className="record-summary">
            <div>
              <strong>{totalScreenings}</strong>
              <span>Screenings</span>
            </div>

            <div>
              <strong>{totalReports}</strong>
              <span>Reports</span>
            </div>

            <div>
              <strong>{suspiciousCount}</strong>
              <span>Suspicious</span>
            </div>
          </div>
        </article>
      </section>

      <section className="emr-panel">
        <div className="emr-panel-title">
          <h2>Previous screenings and reports</h2>

          <span>
            {screenings.length} screening
            {screenings.length === 1 ? "" : "s"} ·{" "}
            {reports.length} report
            {reports.length === 1 ? "" : "s"}
          </span>
        </div>

        {screenings.length > 0 ? (
          <div className="emr-table-wrap flat">
            <table className="emr-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Prediction</th>
                  <th>Confidence</th>
                  <th>Image quality</th>
                  <th>Report</th>
                </tr>
              </thead>

              <tbody>
                {screenings.map((screening) => {
                  const downloadUrl =
                    getDownloadUrl(screening);

                  return (
                    <tr
                      key={
                        screening.id ||
                        screening._id ||
                        screening.screening_id
                      }
                    >
                      <td>
                        {formatDate(
                          screening.created_at
                        )}
                      </td>

                      <td>
                        {String(
                          screening.prediction || "—"
                        ).replaceAll("_", " ")}
                      </td>

                      <td>
                        {formatConfidence(screening)}
                      </td>

                      <td>
                        {screening.image_quality?.status ||
                          screening.image_quality_status ||
                          "—"}
                      </td>

                      <td>
                        {downloadUrl ? (
                          <a
                            className="table-link"
                            href={downloadUrl}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Download PDF
                          </a>
                        ) : screening.report_id ? (
                          <span>
                            {screening.report_id}
                          </span>
                        ) : (
                          "Not generated"
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : reports.length > 0 ? (
          <div className="emr-table-wrap flat">
            <table className="emr-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Report ID</th>
                  <th>Prediction</th>
                  <th>Confidence</th>
                  <th>Download</th>
                </tr>
              </thead>

              <tbody>
                {reports.map((report) => {
                  const downloadUrl =
                    getDownloadUrl(report);

                  return (
                    <tr
                      key={
                        report.id ||
                        report.report_id
                      }
                    >
                      <td>
                        {formatDate(
                          report.created_at ||
                          report.generated_at
                        )}
                      </td>

                      <td>
                        {report.report_id ||
                          report.id ||
                          "—"}
                      </td>

                      <td>
                        {String(
                          report.prediction || "—"
                        ).replaceAll("_", " ")}
                      </td>

                      <td>
                        {formatConfidence(report)}
                      </td>

                      <td>
                        {downloadUrl ? (
                          <a
                            className="table-link"
                            href={downloadUrl}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Download PDF
                          </a>
                        ) : (
                          "Unavailable"
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="emr-empty">
            No previous screenings available.
            Start a new AI screening to create the patient's medical history.
          </div>
        )}
      </section>
    </div>
  );
}

function ReportsPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const searchReports = async () => {
    try {
      setLoading(true);
      setError("");

      const searchText = query.trim();

      const path = searchText
        ? `/api/v1/reports?search=${encodeURIComponent(searchText)}&limit=100`
        : `/api/v1/reports?limit=100`;

      const data = await apiRequest(path);

      setResults(data.reports || []);
    } catch (requestError) {
      console.error("Reports loading error:", requestError);

      setError(
        requestError.message ||
        "Unable to load reports."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    searchReports();
  }, []);

  const getDownloadUrl = (report) => {
    const url = report.download_url;

    if (!url) {
      return "";
    }

    if (
      url.startsWith("http://") ||
      url.startsWith("https://")
    ) {
      return url;
    }

    return `${API_BASE_URL}${url}`;
  };

  const getVerificationUrl = (report) => {
    if (report.verification_url) {
      if (
        report.verification_url.startsWith("http://") ||
        report.verification_url.startsWith("https://")
      ) {
        return report.verification_url;
      }

      return `${API_BASE_URL}${report.verification_url}`;
    }

    if (report.report_id) {
      return `${API_BASE_URL}/api/v1/reports/${report.report_id}/verify`;
    }

    return "";
  };

  return (
    <div className="emr-page">
      <PageHeader
        eyebrow="Documents"
        title="Reports"
        description="Locate, verify, and download generated screening reports."
      />

      <div className="emr-toolbar">
        <input
          value={query}
          onChange={(event) =>
            setQuery(event.target.value)
          }
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              searchReports();
            }
          }}
          placeholder="Search report ID or patient name"
        />

        <button
          type="button"
          onClick={searchReports}
          disabled={loading}
        >
          {loading ? "Searching..." : "Search reports"}
        </button>
      </div>

      {loading ? (
        <LoadingState label="Loading reports..." />
      ) : error ? (
        <ErrorState
          message={error}
          onRetry={searchReports}
        />
      ) : (
        <div className="report-grid">
          {results.map((report) => {
            const downloadUrl =
              getDownloadUrl(report);

            const verificationUrl =
              getVerificationUrl(report);

            return (
              <article
                className="report-card"
                key={report.id || report.report_id}
              >
                <div className="report-icon">
                  PDF
                </div>

                <div>
                  <span>Screening report</span>

                  <h3>
                    {report.report_id ||
                      report.id ||
                      "Report"}
                  </h3>

                  <p>
                    {report.patient_name ||
                      "Unknown patient"}
                    {" · "}
                    {formatDate(
                      report.created_at ||
                      report.generated_at
                    )}
                  </p>

                  <p>
                    Prediction:{" "}
                    <strong>
                      {String(
                        report.prediction || "—"
                      ).replaceAll("_", " ")}
                    </strong>
                  </p>

                  <p>
                    Confidence:{" "}
                    <strong>
                      {report.confidence_percent !==
                        undefined &&
                        report.confidence_percent !== null
                        ? `${Number(
                          report.confidence_percent
                        ).toFixed(2)}%`
                        : "—"}
                    </strong>
                  </p>
                </div>

                <div className="report-card-actions">
                  {downloadUrl && (
                    <a
                      href={downloadUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Download
                    </a>
                  )}

                  {verificationUrl && (
                    <a
                      href={verificationUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Verify
                    </a>
                  )}
                </div>
              </article>
            );
          })}

          {!results.length && (
            <div className="emr-empty full">
              No reports available.
              Generate a report from the Screening page.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SearchPage() {
  const [query, setQuery] = useState(""); const [data, setData] = useState(null); const [loading, setLoading] = useState(false); const [error, setError] = useState(""); const navigate = useNavigate();
  const run = async () => { if (!query.trim()) return; try { setLoading(true); setError(''); setData(await apiRequest(`/api/v1/search?query=${encodeURIComponent(query.trim())}`)); } catch (e) { setError(e.message) } finally { setLoading(false) } };
  const patients = data?.patients || data?.results?.patients || []; const screenings = data?.screenings || data?.results?.screenings || []; const reports = data?.reports || data?.results?.reports || [];
  return <div className="emr-page"><PageHeader eyebrow="Global finder" title="Search" description="Search patients, screenings, and reports from one place." /><div className="search-hero"><input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && run()} placeholder="Enter patient name, phone, patient ID, or report ID" /><button onClick={run}>Search</button></div>{loading ? <LoadingState /> : error ? <ErrorState message={error} /> : data && <div className="search-groups"><SearchGroup title="Patients" count={patients.length}>{patients.map(p => <button key={p.id} onClick={() => navigate(`/patients/${p.id}`)}><strong>{p.patient_name}</strong><small>{p.phone || p.id}</small></button>)}</SearchGroup><SearchGroup title="Screenings" count={screenings.length}>{screenings.map(s => <div key={s.id || s._id}><strong>{String(s.prediction || 'Screening').replaceAll('_', ' ')}</strong><small>{formatDate(s.created_at)}</small></div>)}</SearchGroup><SearchGroup title="Reports" count={reports.length}>{reports.map(r => <div key={r.id || r.report_id}><strong>{r.report_id || r.id}</strong><small>{r.patient_name || formatDate(r.created_at)}</small></div>)}</SearchGroup></div>}</div>;
}
function SearchGroup({ title, count, children }) { return <section className="emr-panel search-group"><div className="emr-panel-title"><h2>{title}</h2><span>{count}</span></div><div className="search-results">{count ? children : <p className="emr-muted">No matches.</p>}</div></section> }



function StatisticsPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const loadStatistics = async () => {
    try {
      setRefreshing(true);
      setError("");
      setStats(await apiRequest("/api/v1/dashboard/stats"));
    } catch (requestError) {
      setError(
        requestError.message ||
        "Unable to load analytics."
      );
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadStatistics();
  }, []);

  if (error) {
    return (
      <div className="emr-page">
        <ErrorState
          message={error}
          onRetry={loadStatistics}
        />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="emr-page">
        <LoadingState label="Loading analytics dashboard..." />
      </div>
    );
  }

  const summary = stats.summary || {};

  const numberValue = (value) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const titleCase = (value) =>
    String(value || "Unknown")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());

  const monthlyScreenings = (
    Array.isArray(stats.monthly_screenings)
      ? stats.monthly_screenings
      : []
  ).map((item) => ({
    month: item.month || item.month_key || "—",
    screenings: numberValue(
      item.screenings ?? item.count
    ),
  }));

  const monthlyReports = (
    Array.isArray(stats.monthly_reports)
      ? stats.monthly_reports
      : []
  ).map((item) => ({
    month: item.month || item.month_key || "—",
    reports: numberValue(
      item.reports ?? item.count
    ),
  }));

  const confidenceTrend = (
    Array.isArray(stats.confidence_trend)
      ? stats.confidence_trend
      : []
  ).map((item) => ({
    month: item.month || item.month_key || "—",
    confidence: numberValue(
      item.average_confidence ??
      item.confidence ??
      item.value
    ),
  }));

  const outcomeSource =
    stats.outcome_distribution || {};

  const suspiciousCases = numberValue(
    outcomeSource.suspicious ??
    outcomeSource.cancer ??
    summary.suspicious_cases ??
    summary.cancer_cases
  );

  const nonCancerCases = numberValue(
    outcomeSource.non_cancer ??
    outcomeSource.nonCancer ??
    summary.non_cancer_cases
  );

  const outcomeData = [
    {
      name: "Suspicious",
      value: suspiciousCases,
    },
    {
      name: "Non-Cancer",
      value: nonCancerCases,
    },
  ];

  const qualitySource =
    stats.quality_distribution || {};

  const qualityData = Array.isArray(qualitySource)
    ? qualitySource.map((item) => ({
      name: titleCase(
        item.name ||
        item.status ||
        item.label
      ),
      value: numberValue(
        item.value ?? item.count
      ),
    }))
    : Object.entries(qualitySource).map(
      ([name, value]) => ({
        name: titleCase(name),
        value: numberValue(value),
      })
    );

  const hasOutcomeData = outcomeData.some(
    (item) => item.value > 0
  );

  const analyticsCards = [
    {
      title: "Total Patients",
      value: numberValue(summary.total_patients),
      icon: "👥",
      tone: "blue",
      note: "Registered patient records",
    },
    {
      title: "Total Screenings",
      value: numberValue(summary.total_screenings),
      icon: "🩺",
      tone: "purple",
      note: "AI analyses completed",
    },
    {
      title: "Suspicious Cases",
      value: numberValue(
        summary.cancer_cases ??
        summary.suspicious_cases
      ),
      icon: "!",
      tone: "red",
      note: "Require clinical review",
    },
    {
      title: "Non-Cancer Cases",
      value: numberValue(
        summary.non_cancer_cases
      ),
      icon: "✓",
      tone: "green",
      note: "Lower-risk screening results",
    },
    {
      title: "Today's Reports",
      value: numberValue(summary.today_reports),
      icon: "PDF",
      tone: "orange",
      note: "Reports generated today",
    },
    {
      title: "Average Confidence",
      value: `${numberValue(
        summary.average_confidence
      ).toFixed(1)}%`,
      icon: "◎",
      tone: "cyan",
      note: "Mean model confidence",
    },
    {
      title: "Poor Quality Images",
      value: numberValue(
        summary.poor_quality_images
      ),
      icon: "⚠",
      tone: "yellow",
      note: "Need image recapture",
    },
  ];

  const chartTooltipStyle = {
    background: "var(--surface-solid)",
    border: "1px solid var(--border)",
    borderRadius: "12px",
    boxShadow: "var(--shadow-small)",
    color: "var(--text-primary)",
  };

  const axisTick = {
    fill: "var(--text-muted)",
    fontSize: 11,
  };

  const chartColors = {
    primary: "#0d9488",
    secondary: "#2563eb",
    danger: "#dc5a63",
    success: "#22a06b",
    warning: "#d99825",
    purple: "#7c3aed",
    grid: "rgba(128, 148, 151, 0.18)",
  };

  return (
    <div className="emr-page analytics-page">
      <PageHeader
        eyebrow="Analytics"
        title="Statistics Dashboard"
        description="Interactive clinical trends from patient records, AI screenings, reports, confidence scores, and image quality."
        action={
          <button
            type="button"
            className="emr-secondary analytics-refresh"
            onClick={loadStatistics}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "↻ Refresh"}
          </button>
        }
      />

      <section className="analytics-cards-grid">
        {analyticsCards.map((card) => (
          <article
            key={card.title}
            className={`analytics-card analytics-card-${card.tone}`}
          >
            <div className="analytics-icon">
              {card.icon}
            </div>

            <div className="analytics-card-content">
              <span>{card.title}</span>
              <strong>{card.value}</strong>
              <small>{card.note}</small>
            </div>
          </article>
        ))}
      </section>

      <section className="analytics-chart-grid">
        <article className="emr-panel analytics-chart-card">
          <div className="emr-panel-title analytics-chart-title">
            <div>
              <h2>Outcome Distribution</h2>
              <p>Suspicious versus non-cancer screening outcomes.</p>
            </div>
            <span>{suspiciousCases + nonCancerCases} outcomes</span>
          </div>

          <div className="analytics-chart-body">
            {hasOutcomeData ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={outcomeData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="48%"
                    innerRadius={66}
                    outerRadius={102}
                    paddingAngle={3}
                    labelLine={false}
                    label={({ percent }) =>
                      `${Math.round(percent * 100)}%`
                    }
                  >
                    <Cell fill={chartColors.danger} />
                    <Cell fill={chartColors.success} />
                  </Pie>

                  <Tooltip
                    contentStyle={chartTooltipStyle}
                    formatter={(value) => [
                      Number(value).toLocaleString(),
                      "Cases",
                    ]}
                  />

                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="analytics-empty">
                No screening outcomes available.
              </div>
            )}
          </div>
        </article>

        <article className="emr-panel analytics-chart-card">
          <div className="emr-panel-title analytics-chart-title">
            <div>
              <h2>Monthly Screenings</h2>
              <p>AI screening volume over the last 12 months.</p>
            </div>
          </div>

          <div className="analytics-chart-body">
            {monthlyScreenings.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={monthlyScreenings}
                  margin={{
                    top: 10,
                    right: 18,
                    left: -14,
                    bottom: 4,
                  }}
                >
                  <CartesianGrid
                    stroke={chartColors.grid}
                    strokeDasharray="4 4"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="month"
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={18}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={chartTooltipStyle}
                    formatter={(value) => [
                      Number(value).toLocaleString(),
                      "Screenings",
                    ]}
                  />
                  <Line
                    type="monotone"
                    dataKey="screenings"
                    name="Screenings"
                    stroke={chartColors.primary}
                    strokeWidth={3}
                    dot={{
                      r: 4,
                      fill: chartColors.primary,
                      strokeWidth: 0,
                    }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="analytics-empty">
                No monthly screening data available.
              </div>
            )}
          </div>
        </article>

        <article className="emr-panel analytics-chart-card">
          <div className="emr-panel-title analytics-chart-title">
            <div>
              <h2>Monthly Reports</h2>
              <p>PDF screening reports generated each month.</p>
            </div>
          </div>

          <div className="analytics-chart-body">
            {monthlyReports.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={monthlyReports}
                  margin={{
                    top: 10,
                    right: 18,
                    left: -14,
                    bottom: 4,
                  }}
                >
                  <CartesianGrid
                    stroke={chartColors.grid}
                    strokeDasharray="4 4"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="month"
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={18}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={chartTooltipStyle}
                    cursor={{
                      fill: "rgba(13, 148, 136, 0.07)",
                    }}
                    formatter={(value) => [
                      Number(value).toLocaleString(),
                      "Reports",
                    ]}
                  />
                  <Bar
                    dataKey="reports"
                    name="Reports"
                    fill={chartColors.secondary}
                    radius={[8, 8, 2, 2]}
                    maxBarSize={34}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="analytics-empty">
                No monthly report data available.
              </div>
            )}
          </div>
        </article>

        <article className="emr-panel analytics-chart-card">
          <div className="emr-panel-title analytics-chart-title">
            <div>
              <h2>Confidence Trend</h2>
              <p>Average model confidence by month.</p>
            </div>
            <span>
              {numberValue(
                summary.average_confidence
              ).toFixed(1)}
              % average
            </span>
          </div>

          <div className="analytics-chart-body">
            {confidenceTrend.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={confidenceTrend}
                  margin={{
                    top: 10,
                    right: 18,
                    left: -8,
                    bottom: 4,
                  }}
                >
                  <defs>
                    <linearGradient
                      id="confidenceGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor={chartColors.purple}
                        stopOpacity={0.35}
                      />
                      <stop
                        offset="95%"
                        stopColor={chartColors.purple}
                        stopOpacity={0.02}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    stroke={chartColors.grid}
                    strokeDasharray="4 4"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="month"
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={18}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip
                    contentStyle={chartTooltipStyle}
                    formatter={(value) => [
                      `${Number(value).toFixed(2)}%`,
                      "Average confidence",
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="confidence"
                    name="Average confidence"
                    stroke={chartColors.purple}
                    strokeWidth={3}
                    fill="url(#confidenceGradient)"
                    dot={{
                      r: 3,
                      fill: chartColors.purple,
                      strokeWidth: 0,
                    }}
                    activeDot={{ r: 6 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="analytics-empty">
                No confidence trend data available.
              </div>
            )}
          </div>
        </article>

        <article className="emr-panel analytics-chart-card analytics-chart-wide">
          <div className="emr-panel-title analytics-chart-title">
            <div>
              <h2>Image Quality Distribution</h2>
              <p>
                Quality status assigned before model inference.
              </p>
            </div>
            <span>
              {numberValue(
                summary.poor_quality_images
              )} poor-quality images
            </span>
          </div>

          <div className="analytics-chart-body analytics-chart-body-wide">
            {qualityData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={qualityData}
                  layout="vertical"
                  margin={{
                    top: 8,
                    right: 28,
                    left: 12,
                    bottom: 4,
                  }}
                >
                  <CartesianGrid
                    stroke={chartColors.grid}
                    strokeDasharray="4 4"
                    horizontal={false}
                  />
                  <XAxis
                    type="number"
                    allowDecimals={false}
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={110}
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={chartTooltipStyle}
                    cursor={{
                      fill: "rgba(217, 152, 37, 0.07)",
                    }}
                    formatter={(value) => [
                      Number(value).toLocaleString(),
                      "Images",
                    ]}
                  />
                  <Bar
                    dataKey="value"
                    name="Images"
                    fill={chartColors.warning}
                    radius={[0, 8, 8, 0]}
                    maxBarSize={30}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="analytics-empty">
                No image-quality statistics available.
              </div>
            )}
          </div>
        </article>
      </section>

      <div className="analytics-updated">
        Last updated: {formatDate(stats.generated_at)}
      </div>
    </div>
  );
}


function SettingsPage() {
  const defaultSettings = {
    hospitalName: "OralVision",
    doctorName: "",
    confidenceThreshold: 70,
    requirePatient: true,
    disclaimer:
      "This system provides preliminary risk screening only. Cancer confirmation requires examination and biopsy by a qualified medical professional.",
  };

  const [settings, setSettings] = useState(() => {
    try {
      const saved =
        localStorage.getItem("oralvision-settings") ||
        localStorage.getItem("oralscan-settings");

      return saved
        ? { ...defaultSettings, ...JSON.parse(saved) }
        : defaultSettings;
    } catch {
      return defaultSettings;
    }
  });

  const [saved, setSaved] = useState(false);

  const modelMetadata = [
    ["Product", "OralVision"],
    ["Version", "v1.0"],
    ["AI model", "EfficientNet-B0"],
    ["Framework", "PyTorch"],
    ["Dataset", "Kaggle Oral Cancer Image Dataset"],
    ["Image size", "224 × 224 pixels"],
    ["Classes", "Cancer / Non-Cancer"],
    ["Explainability", "Grad-CAM"],
    ["Backend", "FastAPI"],
    ["Database", "MongoDB Atlas"],
  ];

  const performanceMetadata = [
    ["Test accuracy", "87.10%"],
    ["Sensitivity", "85.42%"],
    ["Specificity", "88.89%"],
    ["ROC-AUC", "0.9292"],
    ["Last trained", "24 July 2026"],
  ];

  const update = (event) => {
    const { name, type, checked, value } = event.target;

    setSettings((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const save = (event) => {
    event.preventDefault();

    localStorage.setItem(
      "oralvision-settings",
      JSON.stringify(settings)
    );

    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="emr-page">
      <PageHeader
        eyebrow="Configuration"
        title="Settings"
        description="Review OralVision model information and customize local screening defaults."
      />

      <section className="settings-metadata-grid">
        <article className="emr-panel metadata-panel">
          <div className="emr-panel-title">
            <h2>Model information</h2>
            <span>OralVision v1.0</span>
          </div>

          <div className="metadata-list">
            {modelMetadata.map(([label, value]) => (
              <div key={label} className="metadata-item">
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="emr-panel metadata-panel">
          <div className="emr-panel-title">
            <h2>Model performance</h2>
            <span>Evaluation results</span>
          </div>

          <div className="performance-grid">
            {performanceMetadata.map(([label, value]) => (
              <div key={label} className="performance-card">
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>

          <div className="metadata-disclaimer">
            These values describe the current academic model and
            must not be interpreted as a clinical diagnosis.
          </div>
        </article>
      </section>

      <form className="settings-form emr-panel" onSubmit={save}>
        <div className="emr-panel-title settings-form-title">
          <h2>Screening defaults</h2>
          <span>Saved on this device</span>
        </div>

        <label>
          <span>Hospital / project name</span>
          <input
            name="hospitalName"
            value={settings.hospitalName || ""}
            onChange={update}
            placeholder="OralVision"
          />
        </label>

        <label>
          <span>Default doctor name</span>
          <input
            name="doctorName"
            value={settings.doctorName || ""}
            onChange={update}
            placeholder="Enter reviewing doctor"
          />
        </label>

        <label>
          <span>Confidence threshold (%)</span>
          <input
            type="number"
            min="0"
            max="100"
            name="confidenceThreshold"
            value={settings.confidenceThreshold ?? 70}
            onChange={update}
          />
        </label>

        <label className="switch-row">
          <span>
            <b>Require patient details</b>
            <small>
              Prevent screening until mandatory fields are valid.
            </small>
          </span>

          <input
            type="checkbox"
            name="requirePatient"
            checked={Boolean(settings.requirePatient)}
            onChange={update}
          />
        </label>

        <label className="full">
          <span>Default medical disclaimer</span>
          <textarea
            name="disclaimer"
            rows="4"
            value={settings.disclaimer || ""}
            onChange={update}
          />
        </label>

        <div className="settings-actions">
          <button className="emr-primary" type="submit">
            Save settings
          </button>

          {saved && (
            <span className="save-success">
              ✓ Settings saved locally
            </span>
          )}
        </div>
      </form>
    </div>
  );
}

function App() {
  const [darkMode, setDarkMode] = useState(
    () =>
      (localStorage.getItem("oralvision-theme") ||
        localStorage.getItem("oralscan-theme")) ===
      "dark"
  );

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      darkMode ? "dark" : "light"
    );

    localStorage.setItem(
      "oralvision-theme",
      darkMode ? "dark" : "light"
    );
  }, [darkMode]);

  return (
    <Shell
      darkMode={darkMode}
      setDarkMode={setDarkMode}
    />
  );
}

export default App;