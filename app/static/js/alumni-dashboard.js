import React, { useEffect, useMemo, useState } from "https://esm.sh/react@18.2.0";
import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";
import {
  Award,
  Bell,
  BookOpenText,
  BriefcaseBusiness,
  Building2,
  CalendarClock,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  ExternalLink,
  FileText,
  GraduationCap,
  HandCoins,
  Handshake,
  Home,
  Linkedin,
  MapPin,
  Menu,
  MessageCircle,
  Newspaper,
  PenLine,
  Plus,
  RefreshCw,
  Rocket,
  Search,
  Send,
  Sparkles,
  UserRound,
  UsersRound,
  X,
} from "https://esm.sh/lucide-react@0.468.0?deps=react@18.2.0";

const h = React.createElement;
const storeKey = "smart-campus-advanced-alumni-profile";

const skillOptions = ["React", "Python", "Product Management", "UI/UX", "Data Science", "Cloud", "Cybersecurity", "AI/ML"];
const guidanceOptions = ["Mock Interviews", "Resume Review", "Career Counseling", "Hackathon Mentorship"];
const clubOptions = ["Coding Club", "Sports Team", "Robotics Society", "Cultural Committee", "Entrepreneurship Cell"];

const blankProfile = {
  fullName: "",
  batchYear: "",
  department: "",
  company: "",
  designation: "",
  cityCountry: "",
  skills: [],
  industryDomain: "EdTech",
  publications: "",
  mentorshipAvailable: false,
  guidanceAreas: [],
  weeklyAvailability: "1 Hour/Week",
  startupName: "",
  startupWebsite: "",
  fundingStage: "Bootstrapped",
  hiringInterns: false,
  angelInvesting: false,
  hostel: "",
  clubs: [],
  favoriteSpot: "",
};

const linkedInProfile = {
  fullName: "Aarav Sharma",
  batchYear: "2018",
  department: "Computer Science Engineering",
  company: "Microsoft",
  designation: "Principal Frontend Engineer",
  cityCountry: "Bengaluru, India",
  skills: ["React", "Product Management", "Cloud", "UI/UX"],
  industryDomain: "EdTech",
  publications: "Co-authored a paper on adaptive learning dashboards and holds a design-system patent filing.",
};

const refreshedProfile = {
  company: "Google",
  designation: "Staff Software Engineer",
  cityCountry: "Hyderabad, India",
  skills: ["React", "AI/ML", "Cloud", "Product Management"],
};

const seedJobs = [
  {
    id: 1,
    title: "Frontend Engineer",
    company: "Microsoft",
    type: "Full-time",
    location: "Bengaluru",
    salary: "18-24 LPA",
    description: "Join a product engineering team building polished collaboration surfaces. The role needs strong React fundamentals, component architecture judgment, and comfort working with designers on high-fidelity user experiences.",
  },
  {
    id: 2,
    title: "Product Design Intern",
    company: "Zeta",
    type: "Internship",
    location: "Remote",
    salary: "35k/month",
    description: "A focused internship for students strong in UI/UX, product research, and prototyping. The selected candidate will work on design audits, interaction specs, and usability improvements.",
  },
];

const previousJobs = [
  {
    id: "prev-1",
    title: "Backend Engineering Intern",
    company: "Microsoft",
    type: "Internship",
    location: "Hyderabad",
    salary: "45k/month",
    applicantCount: 18,
    status: "Closed",
    description: "A previous internship posting for API platform work, database modeling, and internal tooling. The role is closed but can be reposted for the next hiring cycle.",
  },
  {
    id: "prev-2",
    title: "Associate Product Analyst",
    company: "Razorpay",
    type: "Full-time",
    location: "Bengaluru",
    salary: "12-16 LPA",
    applicantCount: 24,
    status: "Archived",
    description: "A prior full-time analyst opening focused on funnel metrics, experimentation, and product insights for fintech workflows.",
  },
  {
    id: "prev-3",
    title: "Remote UI Engineer",
    company: "Freshworks",
    type: "Remote",
    location: "Remote",
    salary: "16-20 LPA",
    applicantCount: 11,
    status: "Filled",
    description: "A completed remote frontend role for design-system improvements, component documentation, and accessibility refinements.",
  },
];

const seedApplicants = [
  { id: 1, jobId: 1, name: "Riya Patel", batchBranch: "2026 / CSE", resume: "Resume.pdf", status: "New" },
  { id: 2, jobId: 1, name: "Meera Nair", batchBranch: "2025 / IT", resume: "Portfolio.pdf", status: "Shortlisted" },
  { id: 3, jobId: 1, name: "Arjun Rao", batchBranch: "2026 / ECE", resume: "Resume.pdf", status: "New" },
  { id: 4, jobId: 2, name: "Kabir Khan", batchBranch: "2027 / Design", resume: "CaseStudy.pdf", status: "New" },
  { id: 5, jobId: 2, name: "Sara Thomas", batchBranch: "2026 / IT", resume: "Resume.pdf", status: "Passed" },
];

const seedFeed = [
  {
    id: 1,
    author: "Neha Verma",
    role: "Batch 2017 - Product Manager",
    text: "Opening referral conversations for students interested in analytics and product strategy.",
  },
  {
    id: 2,
    author: "Campus Alumni Office",
    role: "Mentorship Desk",
    text: "Active mentors will be matched with final-year students this week.",
  },
];

function mergeProfile(base, next) {
  return { ...blankProfile, ...base, ...next };
}

const requiredProfileFields = [
  ["Full Name", "fullName", "basic"],
  ["Graduation Batch Year", "batchYear", "basic"],
  ["Academic Department", "department", "basic"],
  ["Current Company", "company", "basic"],
  ["Designation", "designation", "basic"],
  ["Current City/Country", "cityCountry", "basic"],
  ["Core Skills/Technologies", "skills", "expertise"],
  ["Industry Domain", "industryDomain", "expertise"],
  ["Available for Student Mentorship", "mentorshipAvailable", "mentorship"],
  ["Areas of Guidance", "guidanceAreas", "mentorship"],
  ["Weekly Availability", "weeklyAvailability", "mentorship"],
  ["Hostel/Hall of Residence Name", "hostel", "memories"],
  ["Clubs/Societies Joined", "clubs", "memories"],
  ["Favorite Campus Spot", "favoriteSpot", "memories"],
];

function hasValue(value) {
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "boolean") return value;
  return Boolean(String(value || "").trim());
}

function missingRequired(profile, stepKey = "") {
  return requiredProfileFields
    .filter(([, , step]) => !stepKey || step === stepKey)
    .filter(([, key]) => !hasValue(profile[key]))
    .map(([label]) => label);
}

function IconLabel({ icon: Icon, children, className = "" }) {
  return h("span", { className: `inline-flex items-center gap-2 ${className}` }, h(Icon, { size: 16 }), children);
}

function PrimaryButton({ children, icon: Icon, type = "button", onClick, className = "", disabled = false }) {
  return h(
    "button",
    {
      type,
      onClick,
      disabled,
      className: `inline-flex items-center justify-center gap-2 rounded-md bg-[#F59E0B] px-4 py-2.5 text-sm font-bold text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-50 ${className}`,
    },
    Icon ? h(Icon, { size: 17 }) : null,
    children,
  );
}

function SecondaryButton({ children, icon: Icon, type = "button", onClick, className = "", disabled = false }) {
  return h(
    "button",
    {
      type,
      onClick,
      disabled,
      className: `inline-flex items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-[#1E3A8A] transition hover:border-[#1E3A8A] hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50 ${className}`,
    },
    Icon ? h(Icon, { size: 17 }) : null,
    children,
  );
}

function FieldLabel({ label, required = false, optional = false }) {
  return h(
    "span",
    { className: "inline-flex items-center gap-2 font-bold" },
    required ? h("span", { className: "h-2 w-2 rounded-full bg-red-500", title: "Required" }) : null,
    label,
    optional ? h("span", { className: "text-xs font-semibold text-slate-400" }, "(Optional)") : null,
  );
}

function TextField({ label, value, onChange, type = "text", textarea = false, options, required = false, optional = false }) {
  const common = {
    value,
    onChange: (event) => onChange(event.target.value),
    className:
      "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100",
  };
  return h(
    "label",
    { className: "grid gap-2 text-sm text-slate-700" },
    h(FieldLabel, { label, required, optional }),
    options
      ? h("select", common, options.map((option) => h("option", { key: option, value: option }, option)))
      : textarea
        ? h("textarea", { ...common, rows: 4 })
        : h("input", { ...common, type }),
  );
}

function Toggle({ checked, onChange, label, hint }) {
  return h(
    "div",
    { className: "flex items-center justify-between gap-4 rounded-lg border border-slate-100 bg-slate-50 p-4" },
    h("div", null, h("strong", { className: "block text-sm text-slate-900" }, label), hint ? h("span", { className: "text-sm text-slate-500" }, hint) : null),
    h(
      "button",
      {
        type: "button",
        onClick: () => onChange(!checked),
        className: `relative h-7 w-14 shrink-0 rounded-full transition ${checked ? "bg-[#F59E0B]" : "bg-slate-300"}`,
        "aria-pressed": checked,
      },
      h("span", { className: `absolute top-1 h-5 w-5 rounded-full bg-white transition ${checked ? "left-8" : "left-1"}` }),
    ),
  );
}

function BadgeMultiSelect({ label, options, selected, onChange, required = false, optional = false }) {
  const toggle = (item) => {
    onChange(selected.includes(item) ? selected.filter((value) => value !== item) : [...selected, item]);
  };
  return h(
    "div",
    { className: "grid gap-2" },
    h("span", { className: "text-sm text-slate-700" }, h(FieldLabel, { label, required, optional })),
    h(
      "div",
      { className: "flex flex-wrap gap-2" },
      options.map((item) =>
        h(
          "button",
          {
            key: item,
            type: "button",
            onClick: () => toggle(item),
            className: `rounded-full border px-3 py-1.5 text-sm font-bold transition ${
              selected.includes(item)
                ? "border-[#F59E0B] bg-amber-50 text-[#B45309]"
                : "border-slate-200 bg-white text-slate-600 hover:border-[#1E3A8A] hover:text-[#1E3A8A]"
            }`,
          },
          selected.includes(item) ? h(Check, { className: "mr-1 inline", size: 14 }) : null,
          item,
        ),
      ),
    ),
  );
}

function SetupStepShell({ title, subtitle, icon: Icon, children }) {
  return h(
    "section",
    { className: "grid gap-5" },
    h(
      "div",
      { className: "flex items-start gap-3 rounded-lg bg-blue-50 p-4" },
      h("span", { className: "grid h-11 w-11 shrink-0 place-items-center rounded-md bg-[#1E3A8A] text-white" }, h(Icon, { size: 22 })),
      h("div", null, h("h3", { className: "mb-1 text-lg font-bold text-slate-900" }, title), h("p", { className: "text-sm text-slate-600" }, subtitle)),
    ),
    children,
  );
}

function ProfileSetup({ initialProfile, onLaunch }) {
  const steps = [
    ["basic", "Basic Info", UserRound],
    ["expertise", "Expertise", Award],
    ["mentorship", "Mentorship", Handshake],
    ["startup", "Startup", Rocket],
    ["memories", "Memories", GraduationCap],
  ];
  const [profile, setProfile] = useState(() => mergeProfile(initialProfile));
  const [activeStep, setActiveStep] = useState("basic");
  const [validationMessage, setValidationMessage] = useState("");
  const index = steps.findIndex(([key]) => key === activeStep);
  const set = (key) => (value) => setProfile((current) => ({ ...current, [key]: value }));
  const currentMissing = missingRequired(profile, activeStep);
  const allMissing = missingRequired(profile);

  const goNext = () => {
    if (currentMissing.length) {
      setValidationMessage(`Please complete: ${currentMissing.join(", ")}`);
      return;
    }
    setValidationMessage("");
    setActiveStep(steps[index + 1][0]);
  };

  const launchDashboard = () => {
    if (allMissing.length) {
      setValidationMessage(`Complete all important fields before launch: ${allMissing.join(", ")}`);
      return;
    }
    setValidationMessage("");
    onLaunch(profile);
  };

  const syncLinkedIn = () => {
    setProfile((current) => mergeProfile(current, linkedInProfile));
    setValidationMessage("");
  };

  const contentByStep = {
    basic: h(
      SetupStepShell,
      {
        title: "Basic & Professional Info",
        subtitle: "Sync from LinkedIn or fill details manually for city chapters and professional discovery.",
        icon: Linkedin,
      },
      h("div", { className: "flex justify-end" }, h(PrimaryButton, { icon: Linkedin, onClick: syncLinkedIn }, "Sync with LinkedIn")),
      h("div", { className: "grid gap-4 md:grid-cols-2" },
        h(TextField, { label: "Full Name", value: profile.fullName, onChange: set("fullName"), required: true }),
        h(TextField, { label: "Graduation Batch Year", value: profile.batchYear, onChange: set("batchYear"), type: "number", required: true }),
        h(TextField, { label: "Academic Department", value: profile.department, onChange: set("department"), required: true }),
        h(TextField, { label: "Current Company", value: profile.company, onChange: set("company"), required: true }),
        h(TextField, { label: "Designation", value: profile.designation, onChange: set("designation"), required: true }),
        h(TextField, { label: "Current City/Country", value: profile.cityCountry, onChange: set("cityCountry"), required: true }),
      ),
    ),
    expertise: h(
      SetupStepShell,
      {
        title: "Professional Domain & Tech Stack Expertise",
        subtitle: "These tags help students find alumni by domain, tools, and research background.",
        icon: Award,
      },
      h(BadgeMultiSelect, { label: "Core Skills/Technologies", options: skillOptions, selected: profile.skills, onChange: set("skills"), required: true }),
      h(TextField, { label: "Industry Domain", value: profile.industryDomain, onChange: set("industryDomain"), options: ["EdTech", "FinTech", "Healthcare", "SaaS", "Manufacturing", "Consulting"], required: true }),
      h(TextField, { label: "Patents/Research Publications", value: profile.publications, onChange: set("publications"), textarea: true, optional: true }),
    ),
    mentorship: h(
      SetupStepShell,
      {
        title: "Mentorship & Availability Preferences",
        subtitle: "Control whether students can reach out and what type of guidance you prefer to offer.",
        icon: Handshake,
      },
      h(Toggle, { checked: profile.mentorshipAvailable, onChange: set("mentorshipAvailable"), label: "Available for Student Mentorship", hint: profile.mentorshipAvailable ? "You will be visible in mentor matching." : "Turn on when you are ready to guide students." }),
      h(BadgeMultiSelect, { label: "Areas of Guidance", options: guidanceOptions, selected: profile.guidanceAreas, onChange: set("guidanceAreas"), required: true }),
      h(TextField, { label: "Weekly Availability", value: profile.weeklyAvailability, onChange: set("weeklyAvailability"), options: ["1 Hour/Week", "2 Hours/Week", "Weekends Only", "Monthly Office Hours"], required: true }),
    ),
    startup: h(
      SetupStepShell,
      {
        title: "Entrepreneurship & Startup Profile",
        subtitle: "Optional founder or investor information for student startup connects.",
        icon: Rocket,
      },
      h("div", { className: "grid gap-4 md:grid-cols-2" },
        h(TextField, { label: "Startup Name", value: profile.startupName, onChange: set("startupName"), optional: true }),
        h(TextField, { label: "Website URL", value: profile.startupWebsite, onChange: set("startupWebsite"), optional: true }),
        h(TextField, { label: "Funding Stage", value: profile.fundingStage, onChange: set("fundingStage"), options: ["Bootstrapped", "Seed", "Series A+"], optional: true }),
        h("div", { className: "grid gap-3 rounded-lg border border-slate-100 bg-slate-50 p-4" },
          h(Toggle, { checked: profile.hiringInterns, onChange: set("hiringInterns"), label: "Actively Hiring Interns" }),
          h(Toggle, { checked: profile.angelInvesting, onChange: set("angelInvesting"), label: "Interested in Angel Investing in Student Startups" }),
        ),
      ),
    ),
    memories: h(
      SetupStepShell,
      {
        title: "Academic Nostalgia & College Memories",
        subtitle: "Add campus context that makes alumni-student conversations warmer.",
        icon: GraduationCap,
      },
      h("div", { className: "grid gap-4 md:grid-cols-2" },
        h(TextField, { label: "Hostel/Hall of Residence Name", value: profile.hostel, onChange: set("hostel"), required: true }),
        h(TextField, { label: "Favorite Campus Spot", value: profile.favoriteSpot, onChange: set("favoriteSpot"), required: true }),
      ),
      h(BadgeMultiSelect, { label: "Clubs/Societies Joined", options: clubOptions, selected: profile.clubs, onChange: set("clubs"), required: true }),
    ),
  };

  return h(
    "div",
    { className: "overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-slate-100" },
    h(
      "div",
      { className: "bg-[#1E3A8A] px-6 py-6 text-white" },
      h("p", { className: "mb-2 text-xs font-bold uppercase tracking-normal text-amber-200" }, "Comprehensive Alumni Profile"),
      h("h2", { className: "mb-2 text-2xl font-bold text-white" }, "Set up your alumni identity"),
      h("p", { className: "max-w-3xl text-sm text-blue-100" }, "Complete the profile once, then manage jobs, mentorship, content, guidance chats, and startup opportunities from one dashboard."),
    ),
    h(
      "div",
      { className: "grid gap-6 p-6 lg:grid-cols-[260px_1fr]" },
      h(
        "nav",
        { className: "grid content-start gap-2" },
        steps.map(([key, label, Icon], stepIndex) =>
          h(
            "button",
            {
              key,
              type: "button",
              onClick: () => setActiveStep(key),
              className: `flex items-center gap-3 rounded-md px-3 py-3 text-left text-sm font-bold transition ${
                activeStep === key ? "bg-[#1E3A8A] text-white" : "bg-slate-50 text-slate-700 hover:bg-blue-50 hover:text-[#1E3A8A]"
              }`,
            },
            h("span", { className: `grid h-8 w-8 place-items-center rounded-md ${activeStep === key ? "bg-white/15" : "bg-white"}` }, h(Icon, { size: 17 })),
            h("span", null, h("span", { className: "block text-xs opacity-75" }, `Step ${stepIndex + 1}`), label),
          ),
        ),
      ),
      h("div", { className: "grid gap-6" },
        contentByStep[activeStep],
        currentMissing.length ? h("div", { className: "rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-700" }, `Important fields pending in this step: ${currentMissing.join(", ")}`) : null,
        validationMessage ? h("div", { className: "rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-700" }, validationMessage) : null,
        h("div", { className: "flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5" },
          h("div", { className: "flex items-center gap-2 text-sm text-slate-500" }, h(CheckCircle2, { size: 17, className: "text-emerald-600" }), `${index + 1} of ${steps.length} sections active`),
          h("div", { className: "flex flex-wrap gap-2" },
            h(SecondaryButton, { icon: ChevronLeft, onClick: () => setActiveStep(steps[Math.max(index - 1, 0)][0]), className: index === 0 ? "opacity-50" : "" }, "Back"),
            index < steps.length - 1
              ? h(PrimaryButton, { icon: ChevronRight, onClick: goNext, disabled: currentMissing.length > 0 }, "Next")
              : h(PrimaryButton, { icon: Sparkles, onClick: launchDashboard, disabled: allMissing.length > 0 }, "Save and Launch Dashboard"),
          ),
        ),
      ),
    ),
  );
}

function StatCard({ icon: Icon, label, value, tone = "bg-blue-50 text-[#1E3A8A]" }) {
  return h("article", { className: "rounded-lg bg-white p-4 shadow-sm ring-1 ring-slate-100" },
    h("div", { className: "flex items-center justify-between gap-3" },
      h("div", null, h("p", { className: "mb-1 text-sm text-slate-500" }, label), h("strong", { className: "text-2xl text-slate-900" }, value)),
      h("span", { className: `grid h-11 w-11 place-items-center rounded-md ${tone}` }, h(Icon, { size: 22 })),
    ),
  );
}

function DashboardShell({ profile, children, active, setActive }) {
  const [collapsed, setCollapsed] = useState(false);
  const nav = [
    ["overview", "Overview", Home],
    ["give", "Jobs & Internships", BriefcaseBusiness],
    ["content", "Content Hub", Newspaper],
    ["guidance", "Chat/Guidance", MessageCircle],
    ["profile", "Profile", UserRound],
  ];

  return h(
    "div",
    { className: "overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-slate-100" },
    h(
      "div",
      { className: "grid min-h-[680px] lg:grid-cols-[auto_1fr]" },
      h(
        "aside",
        { className: `${collapsed ? "lg:w-20" : "lg:w-72"} border-r border-slate-100 bg-[#1E3A8A] text-white transition-all` },
        h("div", { className: "flex items-center justify-between gap-3 border-b border-white/10 p-4" },
          collapsed ? h("span", { className: "grid h-10 w-10 place-items-center rounded-md bg-[#F59E0B] font-black" }, "A") : h("div", null, h("strong", { className: "block text-lg" }, "Alumni Dashboard"), h("span", { className: "text-xs text-blue-100" }, "Mentorship and career portal")),
          h("button", { type: "button", onClick: () => setCollapsed(!collapsed), className: "grid h-9 w-9 place-items-center rounded-md bg-white/10 text-white hover:bg-white/20" }, collapsed ? h(Menu, { size: 18 }) : h(X, { size: 18 })),
        ),
        h("nav", { className: "grid gap-2 p-3" },
          nav.map(([key, label, Icon]) =>
            h("button", {
              key,
              type: "button",
              onClick: () => setActive(key),
              className: `flex items-center gap-3 rounded-md px-3 py-3 text-sm font-bold transition ${active === key ? "bg-[#F59E0B] text-white" : "text-blue-100 hover:bg-white/10 hover:text-white"}`,
              title: label,
            }, h(Icon, { size: 19 }), collapsed ? null : label),
          ),
        ),
      ),
      h("main", { className: "min-w-0 bg-slate-50" },
        h("header", { className: "border-b border-slate-200 bg-white p-5" },
          h("div", { className: "flex flex-wrap items-start justify-between gap-4" },
            h("div", null,
              h("p", { className: "mb-1 text-xs font-bold uppercase text-[#F59E0B]" }, "Active Alumni Workspace"),
              h("h2", { className: "mb-2 text-2xl font-bold text-slate-900" }, `Welcome, ${profile.fullName || "Alumnus"}`),
              h("div", { className: "flex flex-wrap gap-3 text-sm text-slate-500" },
                h(IconLabel, { icon: BriefcaseBusiness }, `${profile.designation || "Professional"} at ${profile.company || "Company"}`),
                h(IconLabel, { icon: MapPin }, profile.cityCountry || "City Chapter"),
                h(IconLabel, { icon: GraduationCap }, `Batch ${profile.batchYear || "-"}`),
              ),
            ),
            h("div", { className: "rounded-lg border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-900" },
              h("strong", { className: "block" }, profile.mentorshipAvailable ? "Mentorship Active" : "Mentorship Hidden"),
              h("span", null, profile.weeklyAvailability),
            ),
          ),
        ),
        h("div", { className: "grid gap-5 p-5" }, children),
      ),
    ),
  );
}

function ProfileCompletionPanel({ profile }) {
  const required = [
    ["Full Name", profile.fullName],
    ["Batch Year", profile.batchYear],
    ["Department", profile.department],
    ["Company", profile.company],
    ["Designation", profile.designation],
    ["City/Country", profile.cityCountry],
    ["Core Skills", profile.skills.length],
    ["Industry Domain", profile.industryDomain],
    ["Guidance Areas", profile.guidanceAreas.length],
    ["Weekly Availability", profile.weeklyAvailability],
    ["Hostel/Hall", profile.hostel],
    ["Favorite Spot", profile.favoriteSpot],
    ["Clubs/Societies", profile.clubs.length],
  ];
  const optional = [
    ["Patents/Publications", profile.publications],
    ["Startup Name", profile.startupName],
    ["Startup Website", profile.startupWebsite],
    ["Funding Stage", profile.startupName ? profile.fundingStage : ""],
  ];
  const completeCount = required.filter(([, value]) => Boolean(value)).length;

  return h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100" },
    h("div", { className: "mb-4 flex flex-wrap items-center justify-between gap-3" },
      h("div", null,
        h("h3", { className: "text-lg font-bold text-slate-900" }, "Profile Requirements"),
        h("p", { className: "text-sm text-slate-500" }, "Red dot fields are important. Optional fields are clearly marked."),
      ),
      h("span", { className: "rounded-full bg-blue-50 px-3 py-1 text-sm font-bold text-[#1E3A8A]" }, `${completeCount}/${required.length} complete`),
    ),
    h("div", { className: "grid gap-3 md:grid-cols-2 xl:grid-cols-3" },
      required.map(([label, value]) =>
        h("div", { key: label, className: `flex items-center justify-between gap-3 rounded-md border px-3 py-2 ${value ? "border-emerald-100 bg-emerald-50/60" : "border-red-100 bg-red-50/60"}` },
          h("span", { className: "inline-flex items-center gap-2 text-sm font-bold text-slate-700" }, h("span", { className: "h-2 w-2 rounded-full bg-red-500" }), label),
          h("span", { className: `text-xs font-bold ${value ? "text-emerald-700" : "text-red-600"}` }, value ? "Filled" : "Missing"),
        ),
      ),
      optional.map(([label, value]) =>
        h("div", { key: label, className: "flex items-center justify-between gap-3 rounded-md border border-slate-100 bg-slate-50 px-3 py-2" },
          h("span", { className: "text-sm font-bold text-slate-600" }, label, h("span", { className: "ml-2 text-xs font-semibold text-slate-400" }, "(Optional)")),
          h("span", { className: `text-xs font-bold ${value ? "text-emerald-700" : "text-slate-400"}` }, value ? "Added" : "Skip"),
        ),
      ),
    ),
  );
}

function Overview({ profile, jobs, feed }) {
  return h("div", { className: "grid gap-5" },
    h("div", { className: "grid gap-4 md:grid-cols-4" },
      h(StatCard, { icon: Award, label: "Skills", value: profile.skills.length }),
      h(StatCard, { icon: BriefcaseBusiness, label: "Job Posts", value: jobs.length }),
      h(StatCard, { icon: Newspaper, label: "Feed Updates", value: feed.length }),
      h(StatCard, { icon: MessageCircle, label: "Guidance", value: profile.mentorshipAvailable ? "Active" : "Off" }),
    ),
    h("section", { className: "grid gap-4 rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100 lg:grid-cols-[1fr_0.8fr]" },
      h("div", null,
        h("h3", { className: "mb-2 text-lg font-bold text-slate-900" }, "Profile Snapshot"),
        h("p", { className: "mb-4 text-sm text-slate-600" }, profile.publications || "Add publications or patents to strengthen your academic and professional profile."),
        h("div", { className: "flex flex-wrap gap-2" }, profile.skills.map((skill) => h("span", { key: skill, className: "rounded-full bg-blue-50 px-3 py-1 text-sm font-bold text-[#1E3A8A]" }, skill))),
      ),
      h("div", { className: "rounded-lg border border-amber-100 bg-amber-50 p-4" },
        h("h4", { className: "mb-2 font-bold text-slate-900" }, "Startup & Memories"),
        h("p", { className: "text-sm text-slate-700" }, profile.startupName ? `${profile.startupName} - ${profile.fundingStage}` : "Startup profile not added."),
        h("p", { className: "mt-3 text-sm text-slate-700" }, profile.favoriteSpot ? `Favorite campus spot: ${profile.favoriteSpot}` : "Add your favorite campus spot in profile maintenance."),
      ),
    ),
    h(ProfileCompletionPanel, { profile }),
  );
}

function CompanyLogo({ company }) {
  const initials = String(company || "CO").split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  return h("span", { className: "grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#1E3A8A] text-sm font-black text-white shadow-sm" }, initials || "CO");
}

function StatusBadge({ status }) {
  const styles = {
    Shortlisted: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    Passed: "bg-slate-100 text-slate-500 ring-slate-200",
    New: "bg-amber-50 text-[#B45309] ring-amber-100",
  };
  return h("span", { className: `rounded-full px-2.5 py-1 text-xs font-bold ring-1 transition ${styles[status] || styles.New}` }, status);
}

function PostPositionModal({ profile, onClose, onSubmit }) {
  const [form, setForm] = useState({
    title: "",
    company: profile.company || "",
    type: "Full-time",
    location: "",
    salary: "",
    description: "",
  });
  const set = (key) => (value) => setForm((current) => ({ ...current, [key]: value }));

  return h("div", { className: "fixed inset-0 z-[1200] grid place-items-center bg-slate-950/45 p-4 backdrop-blur-sm" },
    h("div", { className: "w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-900/10" },
      h("div", { className: "flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5" },
        h("div", null,
          h("p", { className: "mb-1 text-xs font-bold uppercase tracking-normal text-[#F59E0B]" }, "New Position"),
          h("h3", { className: "text-xl font-bold text-slate-950" }, "Post a position"),
          h("p", { className: "mt-1 text-sm text-slate-500" }, "Create a clean listing for students and alumni applicants."),
        ),
        h("button", { type: "button", onClick: onClose, className: "grid h-9 w-9 place-items-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-700" }, h(X, { size: 18 })),
      ),
      h("form", {
        className: "grid gap-5 px-6 py-5",
        onSubmit: (event) => {
          event.preventDefault();
          if (!form.title.trim() || !form.company.trim()) return;
          onSubmit({ ...form, id: Date.now() });
        },
      },
        h("div", { className: "grid gap-4 md:grid-cols-2" },
          h(TextField, { label: "Job Title", value: form.title, onChange: set("title"), required: true }),
          h(TextField, { label: "Company", value: form.company, onChange: set("company"), required: true }),
        ),
        h("div", { className: "grid gap-4 md:grid-cols-[1fr_1fr]" },
          h("div", { className: "grid gap-2" },
            h(FieldLabel, { label: "Type", required: true }),
            h("div", { className: "grid grid-cols-3 rounded-lg bg-slate-100 p-1" },
              ["Full-time", "Internship", "Remote"].map((type) =>
                h("button", {
                  key: type,
                  type: "button",
                  onClick: () => set("type")(type),
                  className: `rounded-md px-3 py-2 text-xs font-bold transition ${form.type === type ? "bg-white text-[#1E3A8A] shadow-sm" : "text-slate-500 hover:text-slate-900"}`,
                }, type),
              ),
            ),
          ),
          h(TextField, { label: "Location", value: form.location, onChange: set("location"), required: true }),
        ),
        h(TextField, { label: "Salary/Stipend", value: form.salary, onChange: set("salary"), optional: true }),
        h(TextField, { label: "Description", value: form.description, onChange: set("description"), textarea: true, required: true }),
        h("div", { className: "flex justify-end gap-3 border-t border-slate-100 pt-4" },
          h(SecondaryButton, { onClick: onClose }, "Cancel"),
          h(PrimaryButton, { icon: Plus, type: "submit" }, "Post Position"),
        ),
      ),
    ),
  );
}

function GiveBackPortal({ profile, jobs, setJobs }) {
  const [selectedJobId, setSelectedJobId] = useState(jobs[0]?.id || null);
  const [modalOpen, setModalOpen] = useState(false);
  const [applicants, setApplicants] = useState(seedApplicants);
  const [jobQuery, setJobQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");
  const [pipelineFilter, setPipelineFilter] = useState("All");
  const [postingView, setPostingView] = useState("active");
  const allJobs = [...jobs, ...previousJobs];
  const selectedJob = allJobs.find((job) => job.id === selectedJobId) || jobs[0] || previousJobs[0];
  const selectedIsPrevious = previousJobs.some((job) => job.id === selectedJob?.id);
  const visibleApplicants = selectedJob ? applicants.filter((applicant) => applicant.jobId === selectedJob.id) : [];
  const filteredApplicants = pipelineFilter === "All" ? visibleApplicants : visibleApplicants.filter((applicant) => applicant.status === pipelineFilter);
  const sourceJobs = postingView === "active" ? jobs : previousJobs;
  const filteredJobs = sourceJobs.filter((job) => {
    const matchesType = typeFilter === "All" || job.type === typeFilter;
    const haystack = `${job.title} ${job.company} ${job.location} ${job.description}`.toLowerCase();
    return matchesType && haystack.includes(jobQuery.toLowerCase());
  });
  const totalApplicants = applicants.length;
  const countForJob = (job) => job.applicantCount ?? applicants.filter((applicant) => applicant.jobId === job.id).length;
  const updateApplicant = (id, status) => setApplicants((current) => current.map((item) => item.id === id ? { ...item, status } : item));

  const createJob = (job) => {
    setJobs((current) => [job, ...current]);
    setSelectedJobId(job.id);
    setPostingView("active");
    setModalOpen(false);
  };

  const repostJob = (job) => {
    const reposted = {
      ...job,
      id: Date.now(),
      title: `${job.title} (Repost)`,
      applicantCount: undefined,
      status: undefined,
    };
    setJobs((current) => [reposted, ...current]);
    setSelectedJobId(reposted.id);
    setPostingView("active");
  };

  return h("div", { className: "grid gap-5" },
    modalOpen ? h(PostPositionModal, { profile, onClose: () => setModalOpen(false), onSubmit: createJob }) : null,
    h("section", { className: "rounded-2xl bg-white shadow-sm ring-1 ring-slate-100" },
      h("div", { className: "flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-5 py-4" },
        h("div", { className: "flex flex-wrap gap-3" },
          h("div", { className: "rounded-xl border border-slate-100 px-4 py-3" },
            h("p", { className: "text-xs font-bold uppercase text-slate-400" }, "Active Openings"),
            h("strong", { className: "mt-1 block text-2xl text-slate-950" }, jobs.length),
          ),
          h("div", { className: "rounded-xl border border-slate-100 px-4 py-3" },
            h("p", { className: "text-xs font-bold uppercase text-slate-400" }, "Total Applicants"),
            h("strong", { className: "mt-1 block text-2xl text-slate-950" }, totalApplicants),
          ),
          h("div", { className: "rounded-xl border border-slate-100 px-4 py-3" },
            h("p", { className: "text-xs font-bold uppercase text-slate-400" }, "Previous Postings"),
            h("strong", { className: "mt-1 block text-2xl text-slate-950" }, previousJobs.length),
          ),
        ),
        h(PrimaryButton, { icon: Plus, onClick: () => setModalOpen(true), className: "rounded-xl px-5" }, "Post a Position"),
      ),
      h("div", { className: "grid min-h-[620px] lg:grid-cols-[390px_1fr]" },
        h("aside", { className: "border-b border-slate-100 bg-slate-50/70 p-4 lg:border-b-0 lg:border-r" },
          h("div", { className: "mb-4" },
            h("h3", { className: "text-sm font-black uppercase tracking-normal text-slate-500" }, "Your positions"),
            h("p", { className: "mt-1 text-sm text-slate-500" }, "Select a role to inspect details and pipeline."),
          ),
          h("div", { className: "mb-4 grid gap-3" },
            h("label", { className: "relative" },
              h(Search, { className: "absolute left-3 top-2.5 text-slate-400", size: 17 }),
              h("input", { value: jobQuery, onChange: (event) => setJobQuery(event.target.value), placeholder: "Search roles, company, location", className: "w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100" }),
            ),
            h("div", { className: "grid grid-cols-2 gap-2 rounded-xl bg-white p-1 ring-1 ring-slate-100" },
              [["active", "Active postings"], ["previous", "Previous postings"]].map(([key, label]) =>
                h("button", {
                  key,
                  type: "button",
                  onClick: () => {
                    setPostingView(key);
                    setSelectedJobId((key === "active" ? jobs[0] : previousJobs[0])?.id || null);
                  },
                  className: `rounded-lg px-3 py-2 text-xs font-black transition ${postingView === key ? "bg-[#1E3A8A] text-white" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}`,
                }, label),
              ),
            ),
            h("div", { className: "grid grid-cols-4 gap-2 rounded-xl bg-white p-1 ring-1 ring-slate-100" },
              ["All", "Full-time", "Internship", "Remote"].map((type) =>
                h("button", { key: type, type: "button", onClick: () => setTypeFilter(type), className: `rounded-lg px-2 py-2 text-xs font-black transition ${typeFilter === type ? "bg-[#1E3A8A] text-white" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}` }, type),
              ),
            ),
          ),
          h("div", { className: "grid gap-3" }, filteredJobs.map((job) => {
            const active = selectedJob?.id === job.id;
            return h("button", {
              key: job.id,
              type: "button",
              onClick: () => setSelectedJobId(job.id),
              className: `group rounded-2xl border p-4 text-left transition duration-200 ${active ? "border-[#1E3A8A] bg-white shadow-md shadow-blue-950/5 ring-2 ring-blue-100" : "border-slate-100 bg-white hover:-translate-y-0.5 hover:border-slate-200 hover:shadow-md hover:shadow-slate-200/70"}`,
            },
              h("div", { className: "flex gap-3" },
                h(CompanyLogo, { company: job.company }),
                h("div", { className: "min-w-0 flex-1" },
                  h("div", { className: "flex items-start justify-between gap-3" },
                    h("div", { className: "min-w-0" },
                      h("h4", { className: "truncate text-base font-black text-slate-950" }, job.title),
                      h("p", { className: "mt-1 truncate text-sm font-semibold text-slate-500" }, job.company),
                    ),
                    h("span", { className: `rounded-full px-2.5 py-1 text-xs font-black ${active ? "bg-[#F59E0B] text-white" : "bg-blue-50 text-[#1E3A8A]"}` }, job.type),
                  ),
                  h("div", { className: "mt-4 flex items-center justify-between gap-3 text-sm" },
                    h(IconLabel, { icon: MapPin, className: "truncate text-slate-500" }, job.location || "Flexible"),
                    h("span", { className: "shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-500" }, `${countForJob(job)} Applicants`),
                  ),
                  job.status ? h("div", { className: "mt-3 flex items-center justify-between gap-2 border-t border-slate-100 pt-3" },
                    h("span", { className: "rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-500" }, job.status),
                    h("span", { className: "text-xs font-bold text-slate-400" }, "Previous posting"),
                  ) : null,
                ),
              ),
            );
          })),
          filteredJobs.length ? null : h("div", { className: "rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-sm font-bold text-slate-500" }, "No positions match these filters."),
        ),
        h("section", { className: "bg-white p-6" },
          selectedJob ? h("div", { className: "grid gap-6" },
            h("div", { className: "flex flex-wrap items-start justify-between gap-4" },
              h("div", { className: "flex gap-4" },
                h(CompanyLogo, { company: selectedJob.company }),
                h("div", null,
                  h("div", { className: "mb-2 flex flex-wrap gap-2" },
                    h("span", { className: "rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-[#1E3A8A]" }, selectedJob.type),
                    selectedJob.salary ? h("span", { className: "rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-[#B45309]" }, selectedJob.salary) : null,
                  ),
                  h("h3", { className: "text-2xl font-black tracking-normal text-slate-950" }, selectedJob.title),
                  h("p", { className: "mt-1 text-sm font-semibold text-slate-500" }, `${selectedJob.company} - ${selectedJob.location || "Flexible"}`),
                ),
              ),
              selectedIsPrevious
                ? h(PrimaryButton, { icon: Plus, onClick: () => repostJob(selectedJob), className: "rounded-xl" }, "Repost Position")
                : h("button", { type: "button", className: "inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold text-slate-600 transition hover:border-[#1E3A8A] hover:text-[#1E3A8A]" }, h(ExternalLink, { size: 16 }), "Preview"),
            ),
            h("div", { className: "rounded-2xl border border-slate-100 bg-slate-50/70 p-5" },
              h("p", { className: "mb-2 text-xs font-black uppercase text-slate-400" }, "Job Description"),
              h("p", { className: "max-w-3xl text-[15px] leading-7 text-slate-700" }, selectedJob.description || "No description added."),
            ),
            h("div", { className: "grid gap-4" },
              h("div", { className: "flex flex-wrap items-center justify-between gap-3" },
                h("div", null,
                  h("h4", { className: "text-lg font-black text-slate-950" }, selectedIsPrevious ? "Historical Posting" : "Applicant Pipeline"),
                  h("p", { className: "text-sm text-slate-500" }, selectedIsPrevious ? "Previous postings stay visible for reference and quick reposting." : "Review candidates directly in this canvas."),
                ),
                selectedIsPrevious ? h("span", { className: "rounded-full bg-slate-100 px-3 py-1 text-sm font-bold text-slate-500" }, `${selectedJob.applicantCount || 0} previous applicants`) : h("div", { className: "flex flex-wrap items-center gap-2" },
                  ["All", "New", "Shortlisted", "Passed"].map((status) =>
                    h("button", { key: status, type: "button", onClick: () => setPipelineFilter(status), className: `rounded-full px-3 py-1 text-xs font-black transition ${pipelineFilter === status ? "bg-[#F59E0B] text-white" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}` }, status),
                  ),
                  h("span", { className: "rounded-full bg-slate-100 px-3 py-1 text-sm font-bold text-slate-500" }, `${filteredApplicants.length} candidates`),
                ),
              ),
              selectedIsPrevious
                ? h("div", { className: "grid gap-3 md:grid-cols-3" },
                    h("div", { className: "rounded-2xl border border-slate-100 bg-slate-50 p-4" }, h("span", { className: "text-xs font-black uppercase text-slate-400" }, "Applicants"), h("strong", { className: "mt-1 block text-2xl text-slate-950" }, selectedJob.applicantCount || 0)),
                    h("div", { className: "rounded-2xl border border-slate-100 bg-slate-50 p-4" }, h("span", { className: "text-xs font-black uppercase text-slate-400" }, "Status"), h("strong", { className: "mt-1 block text-2xl text-slate-950" }, selectedJob.status || "Previous")),
                    h("div", { className: "rounded-2xl border border-amber-100 bg-amber-50 p-4" }, h("span", { className: "text-xs font-black uppercase text-[#B45309]" }, "Action"), h("button", { type: "button", onClick: () => repostJob(selectedJob), className: "mt-2 rounded-xl bg-[#F59E0B] px-4 py-2 text-sm font-black text-white" }, "Repost now")),
                  )
                : filteredApplicants.length
                ? h("div", { className: "grid gap-3" }, filteredApplicants.map((applicant) =>
                    h("article", { key: applicant.id, className: "grid gap-3 rounded-2xl border border-slate-100 bg-white p-4 transition hover:border-slate-200 hover:shadow-sm md:grid-cols-[1fr_auto] md:items-center" },
                      h("div", { className: "flex items-center gap-3" },
                        h("span", { className: "grid h-10 w-10 place-items-center rounded-full bg-slate-100 text-sm font-black text-[#1E3A8A]" }, applicant.name.split(" ").map((part) => part[0]).join("")),
                        h("div", null,
                          h("strong", { className: "block text-sm text-slate-950" }, applicant.name),
                          h("span", { className: "text-sm text-slate-500" }, applicant.batchBranch),
                        ),
                      ),
                      h("div", { className: "flex flex-wrap items-center gap-2" },
                        h("button", { type: "button", className: "inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-bold text-[#1E3A8A] transition hover:bg-blue-50" }, h(FileText, { size: 15 }), "View Resume"),
                        h(StatusBadge, { status: applicant.status }),
                        h("button", { type: "button", onClick: () => updateApplicant(applicant.id, "Shortlisted"), className: "rounded-lg bg-[#1E3A8A] px-3 py-2 text-xs font-black text-white transition hover:bg-blue-800" }, "Shortlist"),
                        h("button", { type: "button", onClick: () => updateApplicant(applicant.id, "Passed"), className: "rounded-lg border border-slate-200 px-3 py-2 text-xs font-black text-slate-600 transition hover:border-slate-300 hover:bg-slate-50" }, "Pass"),
                      ),
                    ),
                  ))
                : h("div", { className: "rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center" },
                    h("p", { className: "font-bold text-slate-700" }, "No applicants yet"),
                    h("p", { className: "mt-1 text-sm text-slate-500" }, "New applicants will appear here as soon as students apply."),
                  ),
            ),
          ) : h("div", { className: "grid min-h-[460px] place-items-center rounded-2xl border border-dashed border-slate-200 text-center" },
            h("div", null, h(BriefcaseBusiness, { className: "mx-auto mb-3 text-slate-300", size: 34 }), h("p", { className: "font-bold text-slate-700" }, "Post a position to begin")),
          ),
        ),
      ),
    ),
  );
}

function ContentHub({ feed, setFeed }) {
  const [postText, setPostText] = useState("");
  const [article, setArticle] = useState({ title: "", category: "Industry Insight", body: "" });
  const [articles, setArticles] = useState([]);

  return h("div", { className: "grid gap-5 xl:grid-cols-[0.9fr_1.1fr]" },
    h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100" },
      h("h3", { className: "mb-1 text-lg font-bold text-slate-900" }, "Main Newsfeed"),
      h("p", { className: "mb-4 text-sm text-slate-500" }, "Publish professional updates for students and alumni."),
      h("form", {
        className: "grid gap-3",
        onSubmit: (event) => {
          event.preventDefault();
          if (!postText.trim()) return;
          setFeed((current) => [{ id: Date.now(), author: "You", role: "Alumnus", text: postText.trim() }, ...current]);
          setPostText("");
        },
      },
        h("textarea", {
          value: postText,
          onChange: (event) => setPostText(event.target.value),
          placeholder: "Share a role change, referral, hiring tip, learning resource, or campus memory...",
          className: "min-h-28 rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100",
        }),
        h(PrimaryButton, { icon: Send, type: "submit", className: "justify-self-start" }, "Post Update"),
      ),
      h("div", { className: "mt-5 grid gap-3" }, feed.map((item) =>
        h("article", { key: item.id, className: "rounded-lg border border-slate-100 p-4" },
          h("div", { className: "mb-2 flex items-center gap-3" },
            h("span", { className: "grid h-9 w-9 place-items-center rounded-full bg-[#1E3A8A] text-sm font-bold text-white" }, item.author[0]),
            h("div", null, h("strong", { className: "block text-sm text-slate-900" }, item.author), h("span", { className: "text-xs text-slate-500" }, item.role)),
          ),
          h("p", { className: "text-sm text-slate-700" }, item.text),
        ),
      )),
    ),
    h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100" },
      h("h3", { className: "mb-1 text-lg font-bold text-slate-900" }, "Contribute Article"),
      h("p", { className: "mb-4 text-sm text-slate-500" }, "Submit industry insights or tech blogs to the content hub."),
      h("form", {
        className: "grid gap-4",
        onSubmit: (event) => {
          event.preventDefault();
          if (!article.title.trim()) return;
          setArticles((current) => [{ ...article, id: Date.now() }, ...current]);
          setArticle({ title: "", category: "Industry Insight", body: "" });
        },
      },
        h(TextField, { label: "Article Title", value: article.title, onChange: (value) => setArticle({ ...article, title: value }) }),
        h(TextField, { label: "Category", value: article.category, onChange: (value) => setArticle({ ...article, category: value }), options: ["Industry Insight", "Tech Blog", "Career Advice", "Startup Lessons"] }),
        h("div", { className: "rounded-md border border-slate-200" },
          h("div", { className: "flex gap-1 border-b border-slate-100 bg-slate-50 p-2" }, ["B", "I", "H1"].map((tool) => h("span", { key: tool, className: "grid h-8 w-8 place-items-center rounded bg-white text-xs font-bold text-slate-700 ring-1 ring-slate-200" }, tool))),
          h("textarea", { value: article.body, onChange: (event) => setArticle({ ...article, body: event.target.value }), placeholder: "Write your article draft...", className: "min-h-40 w-full border-0 px-3 py-3 text-sm outline-none" }),
        ),
        h(PrimaryButton, { icon: PenLine, type: "submit", className: "justify-self-start" }, "Submit Article"),
      ),
      h("div", { className: "mt-5 grid gap-3" },
        articles.length === 0
          ? h("p", { className: "rounded-md bg-slate-50 p-4 text-sm text-slate-500" }, "Submitted articles will appear here instantly.")
          : articles.map((item) => h("article", { key: item.id, className: "rounded-lg border border-amber-100 bg-amber-50/50 p-4" }, h("span", { className: "text-xs font-bold uppercase text-[#F59E0B]" }, item.category), h("h4", { className: "mt-1 font-bold text-slate-900" }, item.title), h("p", { className: "mt-2 text-sm text-slate-600" }, item.body || "Draft submitted without body text."))),
      ),
    ),
  );
}

const initialRequests = [
  { id: 101, name: "Riya Patel", branchYear: "CSE / 3rd Year", department: "Computer Science", goal: "Resume Review", online: true, unread: 0 },
  { id: 102, name: "Kabir Khan", branchYear: "ECE / Final Year", department: "Electronics", goal: "Mock Interview", online: false, unread: 0 },
  { id: 103, name: "Meera Nair", branchYear: "IT / 2nd Year", department: "Information Technology", goal: "Career Counseling", online: true, unread: 0 },
];

const initialMentees = [
  { id: 201, name: "Arjun Rao", branchYear: "ME / Final Year", department: "Mechanical", goal: "Startup Guidance", online: true, unread: 2 },
  { id: 202, name: "Sara Thomas", branchYear: "CSE / 3rd Year", department: "Computer Science", goal: "Hackathon Mentorship", online: false, unread: 0 },
];

const initialMessages = {
  201: [
    { id: 1, from: "student", text: "Sir, can you review my product internship roadmap?", type: "text" },
    { id: 2, from: "mentor", text: "Yes. Share your current resume and project list first.", type: "text" },
  ],
  202: [
    { id: 1, from: "student", text: "I need help choosing a hackathon problem statement.", type: "text" },
  ],
};

function ChatGuidanceWorkspace() {
  const [panelTab, setPanelTab] = useState("requests");
  const [incoming, setIncoming] = useState(initialRequests);
  const [mentees, setMentees] = useState(initialMentees);
  const [activeId, setActiveId] = useState(initialMentees[0]?.id || null);
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [selectedSlot, setSelectedSlot] = useState("Sat, 4:00 PM");
  const [notes, setNotes] = useState([
    { id: 1, text: "Fix project description", done: false },
    { id: 2, text: "Practice 5 Leetcode arrays", done: true },
  ]);
  const [noteDraft, setNoteDraft] = useState("");
  const activeMentee = mentees.find((mentee) => mentee.id === activeId) || mentees[0];
  const activeMessages = activeMentee ? messages[activeMentee.id] || [] : [];
  const filteredMentees = mentees.filter((mentee) => `${mentee.name} ${mentee.department} ${mentee.goal}`.toLowerCase().includes(search.toLowerCase()));
  const quickReplies = ["Sure, send over your resume!", "Let's catch up this weekend.", "Can you share the problem statement?"];
  const slots = ["Sat, 4:00 PM", "Sun, 11:30 AM", "Wed, 7:00 PM"];

  const appendMessage = (text, type = "text") => {
    if (!activeMentee || !text.trim()) return;
    setMessages((current) => ({
      ...current,
      [activeMentee.id]: [...(current[activeMentee.id] || []), { id: Date.now(), from: "mentor", text: text.trim(), type }],
    }));
    setMentees((current) => current.map((mentee) => mentee.id === activeMentee.id ? { ...mentee, unread: 0 } : mentee));
  };

  const sendDraft = () => {
    appendMessage(draft);
    setDraft("");
  };

  const acceptRequest = (request) => {
    const mentee = { ...request, unread: 1 };
    setIncoming((current) => current.filter((item) => item.id !== request.id));
    setMentees((current) => [mentee, ...current]);
    setMessages((current) => ({
      ...current,
      [mentee.id]: [{ id: Date.now(), from: "student", text: `Hi, I am looking for ${mentee.goal.toLowerCase()} guidance.`, type: "text" }],
    }));
    setActiveId(mentee.id);
    setPanelTab("mentees");
  };

  const addNote = () => {
    if (!noteDraft.trim()) return;
    setNotes((current) => [...current, { id: Date.now(), text: noteDraft.trim(), done: false }]);
    setNoteDraft("");
  };

  return h("section", { className: "overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-slate-100" },
    h("div", { className: "grid min-h-[700px] xl:grid-cols-[360px_1fr]" },
      h("aside", { className: "border-b border-slate-100 bg-slate-50/80 p-4 xl:border-b-0 xl:border-r" },
        h("div", { className: "mb-4" },
          h("p", { className: "text-xs font-black uppercase text-[#F59E0B]" }, "Mentorship Desk"),
          h("h3", { className: "mt-1 text-xl font-black text-slate-950" }, "Chat/Guidance"),
          h("p", { className: "mt-1 text-sm text-slate-500" }, "Accept students, guide active mentees, and track career goals."),
        ),
        h("div", { className: "mb-4 grid grid-cols-2 rounded-xl bg-white p-1 ring-1 ring-slate-100" },
          [["requests", "Incoming Requests"], ["mentees", "Active Mentees"]].map(([key, label]) =>
            h("button", { key, type: "button", onClick: () => setPanelTab(key), className: `rounded-lg px-3 py-2 text-xs font-black transition ${panelTab === key ? "bg-[#1E3A8A] text-white" : "text-slate-500 hover:bg-slate-50"}` }, label),
          ),
        ),
        panelTab === "requests"
          ? h("div", { className: "grid gap-3" },
              incoming.map((request) =>
                h("article", { key: request.id, className: "rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md" },
                  h("div", { className: "mb-3 flex items-start justify-between gap-3" },
                    h("div", null,
                      h("h4", { className: "font-black text-slate-950" }, request.name),
                      h("p", { className: "mt-1 text-sm text-slate-500" }, request.branchYear),
                    ),
                    h("span", { className: "rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-[#B45309]" }, request.goal),
                  ),
                  h("div", { className: "grid grid-cols-2 gap-2" },
                    h(PrimaryButton, { onClick: () => acceptRequest(request), className: "px-3 py-2 text-xs" }, "Accept Connect"),
                    h(SecondaryButton, { onClick: () => setIncoming((current) => current.filter((item) => item.id !== request.id)), className: "px-3 py-2 text-xs" }, "Decline"),
                  ),
                ),
              ),
              incoming.length ? null : h("div", { className: "rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-sm font-bold text-slate-500" }, "No pending requests."),
            )
          : h("div", { className: "grid gap-3" },
              h("label", { className: "relative" },
                h(Search, { className: "absolute left-3 top-2.5 text-slate-400", size: 17 }),
                h("input", { value: search, onChange: (event) => setSearch(event.target.value), placeholder: "Search mentees", className: "w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100" }),
              ),
              filteredMentees.map((mentee) =>
                h("button", { key: mentee.id, type: "button", onClick: () => { setActiveId(mentee.id); setMentees((current) => current.map((item) => item.id === mentee.id ? { ...item, unread: 0 } : item)); }, className: `rounded-2xl border p-4 text-left transition ${activeMentee?.id === mentee.id ? "border-[#1E3A8A] bg-white shadow-md ring-2 ring-blue-100" : "border-slate-100 bg-white hover:border-slate-200 hover:shadow-sm"}` },
                  h("div", { className: "flex items-center gap-3" },
                    h("span", { className: "relative grid h-10 w-10 place-items-center rounded-full bg-[#1E3A8A] text-sm font-black text-white" },
                      mentee.name.split(" ").map((part) => part[0]).join(""),
                      mentee.online ? h("span", { className: "absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" }) : null,
                    ),
                    h("div", { className: "min-w-0 flex-1" },
                      h("strong", { className: "block truncate text-sm text-slate-950" }, mentee.name),
                      h("span", { className: "block truncate text-xs text-slate-500" }, mentee.branchYear),
                    ),
                    mentee.unread ? h("span", { className: "rounded-full bg-amber-50 px-2 py-1 text-xs font-black text-[#B45309]" }, `${mentee.unread} new`) : null,
                  ),
                ),
              ),
            ),
      ),
      h("main", { className: "grid min-w-0 bg-white lg:grid-cols-[1fr_320px]" },
        h("section", { className: "flex min-h-[700px] flex-col border-b border-slate-100 lg:border-b-0 lg:border-r" },
          activeMentee ? h("div", { className: "border-b border-slate-100 p-5" },
            h("div", { className: "flex items-center justify-between gap-3" },
              h("div", null,
                h("h3", { className: "text-xl font-black text-slate-950" }, activeMentee.name),
                h("p", { className: "mt-1 text-sm text-slate-500" }, `${activeMentee.branchYear} - ${activeMentee.goal}`),
              ),
              h("span", { className: `rounded-full px-3 py-1 text-xs font-black ${activeMentee.online ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}` }, activeMentee.online ? "Online" : "Offline"),
            ),
          ) : null,
          h("div", { className: "flex-1 space-y-3 overflow-y-auto bg-slate-50/70 p-5" },
            activeMessages.map((message) =>
              h("div", { key: message.id, className: `flex ${message.from === "mentor" ? "justify-end" : "justify-start"}` },
                h("div", { className: `max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm ${message.from === "mentor" ? "bg-[#1E3A8A] text-white" : "bg-white text-slate-700 ring-1 ring-slate-100"} ${message.type === "meeting" ? "border border-amber-200 bg-amber-50 text-amber-950" : ""}` }, message.text),
              ),
            ),
          ),
          h("div", { className: "border-t border-slate-100 bg-white p-4" },
            h("div", { className: "mb-3 flex flex-wrap gap-2" }, quickReplies.map((reply) =>
              h("button", { key: reply, type: "button", onClick: () => appendMessage(reply), className: "rounded-full border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600 transition hover:border-[#1E3A8A] hover:bg-blue-50 hover:text-[#1E3A8A]" }, reply),
            )),
            h("div", { className: "flex gap-2" },
              h("input", { value: draft, onChange: (event) => setDraft(event.target.value), onKeyDown: (event) => { if (event.key === "Enter") sendDraft(); }, placeholder: "Type guidance message...", className: "min-h-11 flex-1 rounded-xl border border-slate-200 px-3 text-sm outline-none transition focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100" }),
              h("button", { type: "button", onClick: sendDraft, className: "grid h-11 w-11 place-items-center rounded-xl bg-[#F59E0B] text-white transition hover:bg-amber-600" }, h(Send, { size: 18 })),
            ),
          ),
        ),
        h("aside", { className: "grid content-start gap-5 bg-white p-5" },
          h("section", { className: "rounded-2xl border border-slate-100 bg-slate-50 p-4" },
            h("h4", { className: "font-black text-slate-950" }, "Propose Session"),
            h("p", { className: "mt-1 text-sm text-slate-500" }, "Pick a slot and send a structured meeting card."),
            h("div", { className: "mt-4 grid gap-2" }, slots.map((slot) =>
              h("button", { key: slot, type: "button", onClick: () => setSelectedSlot(slot), className: `rounded-xl border px-3 py-2 text-left text-sm font-bold transition ${selectedSlot === slot ? "border-[#F59E0B] bg-amber-50 text-[#B45309]" : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"}` }, slot),
            )),
            h(PrimaryButton, { icon: CalendarClock, onClick: () => appendMessage(`Mentorship session proposed: ${selectedSlot}. Please confirm if this works for you.`, "meeting"), className: "mt-4 w-full rounded-xl" }, "Propose Meeting"),
          ),
          h("section", { className: "rounded-2xl border border-slate-100 bg-white p-4" },
            h("h4", { className: "font-black text-slate-950" }, "Quick Notes & Goals"),
            h("div", { className: "mt-4 grid gap-2" }, notes.map((note) =>
              h("label", { key: note.id, className: "flex items-center gap-3 rounded-xl bg-slate-50 px-3 py-2" },
                h("input", { type: "checkbox", checked: note.done, onChange: () => setNotes((current) => current.map((item) => item.id === note.id ? { ...item, done: !item.done } : item)), className: "h-4 w-4 accent-[#F59E0B]" }),
                h("span", { className: `text-sm font-semibold ${note.done ? "text-slate-400 line-through" : "text-slate-700"}` }, note.text),
              ),
            )),
            h("div", { className: "mt-3 flex gap-2" },
              h("input", { value: noteDraft, onChange: (event) => setNoteDraft(event.target.value), onKeyDown: (event) => { if (event.key === "Enter") addNote(); }, placeholder: "Add action item", className: "min-h-10 flex-1 rounded-xl border border-slate-200 px-3 text-sm outline-none focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100" }),
              h("button", { type: "button", onClick: addNote, className: "grid h-10 w-10 place-items-center rounded-xl bg-[#1E3A8A] text-white" }, h(Plus, { size: 17 })),
            ),
          ),
        ),
      ),
    ),
  );
}

function ProfileMaintenance({ profile, setProfile }) {
  const [synced, setSynced] = useState(false);
  const set = (key) => (value) => setProfile((current) => ({ ...current, [key]: value }));
  return h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100" },
    h("div", { className: "mb-5 flex flex-wrap items-start justify-between gap-4" },
      h("div", null, h("h3", { className: "mb-1 text-lg font-bold text-slate-900" }, "Profile Maintenance"), h("p", { className: "text-sm text-slate-500" }, "Update every field from onboarding and refresh professional info anytime.")),
      h(SecondaryButton, { icon: RefreshCw, onClick: () => { setProfile((current) => mergeProfile(current, refreshedProfile)); setSynced(true); } }, "Re-sync with LinkedIn"),
    ),
    synced ? h("div", { className: "mb-5 inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1.5 text-sm font-bold text-[#B45309]" }, h(Bell, { size: 16 }), "LinkedIn refresh updated company, designation, city, and skills.") : null,
    h("div", { className: "grid gap-6" },
      h(SetupStepShell, { title: "Basic & Professional Info", subtitle: "Personal identity, batch, role, company, and chapter location.", icon: UserRound },
        h("div", { className: "grid gap-4 md:grid-cols-2" },
          h(TextField, { label: "Full Name", value: profile.fullName, onChange: set("fullName"), required: true }),
          h(TextField, { label: "Graduation Batch Year", value: profile.batchYear, onChange: set("batchYear"), type: "number", required: true }),
          h(TextField, { label: "Academic Department", value: profile.department, onChange: set("department"), required: true }),
          h(TextField, { label: "Current Company", value: profile.company, onChange: set("company"), required: true }),
          h(TextField, { label: "Designation", value: profile.designation, onChange: set("designation"), required: true }),
          h(TextField, { label: "Current City/Country", value: profile.cityCountry, onChange: set("cityCountry"), required: true }),
        ),
      ),
      h(SetupStepShell, { title: "Expertise", subtitle: "Skills, industry domain, publications, and patents.", icon: Award },
        h(BadgeMultiSelect, { label: "Core Skills/Technologies", options: skillOptions, selected: profile.skills, onChange: set("skills"), required: true }),
        h(TextField, { label: "Industry Domain", value: profile.industryDomain, onChange: set("industryDomain"), options: ["EdTech", "FinTech", "Healthcare", "SaaS", "Manufacturing", "Consulting"], required: true }),
        h(TextField, { label: "Patents/Research Publications", value: profile.publications, onChange: set("publications"), textarea: true, optional: true }),
      ),
      h(SetupStepShell, { title: "Mentorship & Availability", subtitle: "Availability, guidance areas, and weekly hours.", icon: Handshake },
        h(Toggle, { checked: profile.mentorshipAvailable, onChange: set("mentorshipAvailable"), label: "Available for Student Mentorship" }),
        h(BadgeMultiSelect, { label: "Areas of Guidance", options: guidanceOptions, selected: profile.guidanceAreas, onChange: set("guidanceAreas"), required: true }),
        h(TextField, { label: "Weekly Availability", value: profile.weeklyAvailability, onChange: set("weeklyAvailability"), options: ["1 Hour/Week", "2 Hours/Week", "Weekends Only", "Monthly Office Hours"], required: true }),
      ),
      h(SetupStepShell, { title: "Startup Profile", subtitle: "Optional founder, hiring, and investment preferences.", icon: Rocket },
        h("div", { className: "grid gap-4 md:grid-cols-2" }, h(TextField, { label: "Startup Name", value: profile.startupName, onChange: set("startupName"), optional: true }), h(TextField, { label: "Website URL", value: profile.startupWebsite, onChange: set("startupWebsite"), optional: true }), h(TextField, { label: "Funding Stage", value: profile.fundingStage, onChange: set("fundingStage"), options: ["Bootstrapped", "Seed", "Series A+"], optional: true })),
        h(Toggle, { checked: profile.hiringInterns, onChange: set("hiringInterns"), label: "Actively Hiring Interns" }),
        h(Toggle, { checked: profile.angelInvesting, onChange: set("angelInvesting"), label: "Interested in Angel Investing in Student Startups" }),
      ),
      h(SetupStepShell, { title: "College Memories", subtitle: "Hostel, clubs, societies, and favorite campus spot.", icon: BookOpenText },
        h("div", { className: "grid gap-4 md:grid-cols-2" }, h(TextField, { label: "Hostel/Hall of Residence Name", value: profile.hostel, onChange: set("hostel"), required: true }), h(TextField, { label: "Favorite Campus Spot", value: profile.favoriteSpot, onChange: set("favoriteSpot"), required: true })),
        h(BadgeMultiSelect, { label: "Clubs/Societies Joined", options: clubOptions, selected: profile.clubs, onChange: set("clubs"), required: true }),
      ),
    ),
  );
}

function MainDashboard({ profile, setProfile }) {
  const [active, setActive] = useState("overview");
  const [jobs, setJobs] = useState(seedJobs);
  const [feed, setFeed] = useState(seedFeed);

  const view = {
    overview: h(Overview, { profile, jobs, feed }),
    give: h(GiveBackPortal, { profile, jobs, setJobs }),
    content: h(ContentHub, { feed, setFeed }),
    guidance: h(ChatGuidanceWorkspace),
    profile: h(ProfileMaintenance, { profile, setProfile }),
  }[active];

  return h(DashboardShell, { profile, active, setActive }, view);
}

function App() {
  const root = document.getElementById("alumni-dashboard-root");
  const initialProfile = mergeProfile(blankProfile, {
    fullName: root?.dataset.userName || "",
  });
  const [profile, setProfile] = useState(() => {
    const stored = window.localStorage.getItem(storeKey);
    return stored ? mergeProfile(blankProfile, JSON.parse(stored)) : initialProfile;
  });
  const [setupDone, setSetupDone] = useState(() => Boolean(window.localStorage.getItem(storeKey)));

  useEffect(() => {
    if (setupDone) window.localStorage.setItem(storeKey, JSON.stringify(profile));
  }, [profile, setupDone]);

  return h("div", { className: "grid gap-5" },
    setupDone
      ? h(MainDashboard, { profile, setProfile })
      : h(ProfileSetup, { initialProfile: profile, onLaunch: (nextProfile) => { const merged = mergeProfile(profile, nextProfile); setProfile(merged); setSetupDone(true); window.localStorage.setItem(storeKey, JSON.stringify(merged)); } }),
  );
}

createRoot(document.getElementById("alumni-dashboard-root")).render(h(App));
