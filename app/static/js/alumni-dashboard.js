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
    type: "Job",
    location: "Bengaluru",
    description: "React role for product teams building modern collaboration experiences.",
  },
  {
    id: 2,
    title: "Product Design Intern",
    company: "Zeta",
    type: "Internship",
    location: "Remote",
    description: "Internship for students strong in UI/UX, research, and prototyping.",
  },
];

const seedApplicants = [
  { id: 1, name: "Riya Patel", role: "Frontend Engineer", department: "CSE", status: "Resume Pending" },
  { id: 2, name: "Kabir Khan", role: "Product Design Intern", department: "IT", status: "Shortlisted" },
  { id: 3, name: "Meera Nair", role: "Frontend Engineer", department: "ECE", status: "New" },
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

const studentDirectory = [
  { id: 1, name: "Riya Patel", department: "Computer Science", interests: "React internships, portfolio review, mock interviews" },
  { id: 2, name: "Kabir Khan", department: "Electronics", interests: "IoT startups, embedded systems, resume review" },
  { id: 3, name: "Meera Nair", department: "Information Technology", interests: "Cloud roadmap, DevOps projects, career counseling" },
  { id: 4, name: "Arjun Rao", department: "Mechanical", interests: "Product management, entrepreneurship, angel investing" },
];

function mergeProfile(base, next) {
  return { ...blankProfile, ...base, ...next };
}

function IconLabel({ icon: Icon, children, className = "" }) {
  return h("span", { className: `inline-flex items-center gap-2 ${className}` }, h(Icon, { size: 16 }), children);
}

function PrimaryButton({ children, icon: Icon, type = "button", onClick, className = "" }) {
  return h(
    "button",
    {
      type,
      onClick,
      className: `inline-flex items-center justify-center gap-2 rounded-md bg-[#F59E0B] px-4 py-2.5 text-sm font-bold text-white transition hover:bg-amber-600 ${className}`,
    },
    Icon ? h(Icon, { size: 17 }) : null,
    children,
  );
}

function SecondaryButton({ children, icon: Icon, type = "button", onClick, className = "" }) {
  return h(
    "button",
    {
      type,
      onClick,
      className: `inline-flex items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-[#1E3A8A] transition hover:border-[#1E3A8A] hover:bg-blue-50 ${className}`,
    },
    Icon ? h(Icon, { size: 17 }) : null,
    children,
  );
}

function TextField({ label, value, onChange, type = "text", textarea = false, options }) {
  const common = {
    value,
    onChange: (event) => onChange(event.target.value),
    className:
      "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100",
  };
  return h(
    "label",
    { className: "grid gap-2 text-sm text-slate-700" },
    h("span", { className: "font-bold" }, label),
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

function BadgeMultiSelect({ label, options, selected, onChange }) {
  const toggle = (item) => {
    onChange(selected.includes(item) ? selected.filter((value) => value !== item) : [...selected, item]);
  };
  return h(
    "div",
    { className: "grid gap-2" },
    h("span", { className: "text-sm font-bold text-slate-700" }, label),
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
  const index = steps.findIndex(([key]) => key === activeStep);
  const set = (key) => (value) => setProfile((current) => ({ ...current, [key]: value }));

  const syncLinkedIn = () => {
    setProfile((current) => mergeProfile(current, linkedInProfile));
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
        h(TextField, { label: "Full Name", value: profile.fullName, onChange: set("fullName") }),
        h(TextField, { label: "Graduation Batch Year", value: profile.batchYear, onChange: set("batchYear"), type: "number" }),
        h(TextField, { label: "Academic Department", value: profile.department, onChange: set("department") }),
        h(TextField, { label: "Current Company", value: profile.company, onChange: set("company") }),
        h(TextField, { label: "Designation", value: profile.designation, onChange: set("designation") }),
        h(TextField, { label: "Current City/Country", value: profile.cityCountry, onChange: set("cityCountry") }),
      ),
    ),
    expertise: h(
      SetupStepShell,
      {
        title: "Professional Domain & Tech Stack Expertise",
        subtitle: "These tags help students find alumni by domain, tools, and research background.",
        icon: Award,
      },
      h(BadgeMultiSelect, { label: "Core Skills/Technologies", options: skillOptions, selected: profile.skills, onChange: set("skills") }),
      h(TextField, { label: "Industry Domain", value: profile.industryDomain, onChange: set("industryDomain"), options: ["EdTech", "FinTech", "Healthcare", "SaaS", "Manufacturing", "Consulting"] }),
      h(TextField, { label: "Patents/Research Publications", value: profile.publications, onChange: set("publications"), textarea: true }),
    ),
    mentorship: h(
      SetupStepShell,
      {
        title: "Mentorship & Availability Preferences",
        subtitle: "Control whether students can reach out and what type of guidance you prefer to offer.",
        icon: Handshake,
      },
      h(Toggle, { checked: profile.mentorshipAvailable, onChange: set("mentorshipAvailable"), label: "Available for Student Mentorship", hint: profile.mentorshipAvailable ? "You will be visible in mentor matching." : "Turn on when you are ready to guide students." }),
      h(BadgeMultiSelect, { label: "Areas of Guidance", options: guidanceOptions, selected: profile.guidanceAreas, onChange: set("guidanceAreas") }),
      h(TextField, { label: "Weekly Availability", value: profile.weeklyAvailability, onChange: set("weeklyAvailability"), options: ["1 Hour/Week", "2 Hours/Week", "Weekends Only", "Monthly Office Hours"] }),
    ),
    startup: h(
      SetupStepShell,
      {
        title: "Entrepreneurship & Startup Profile",
        subtitle: "Optional founder or investor information for student startup connects.",
        icon: Rocket,
      },
      h("div", { className: "grid gap-4 md:grid-cols-2" },
        h(TextField, { label: "Startup Name", value: profile.startupName, onChange: set("startupName") }),
        h(TextField, { label: "Website URL", value: profile.startupWebsite, onChange: set("startupWebsite") }),
        h(TextField, { label: "Funding Stage", value: profile.fundingStage, onChange: set("fundingStage"), options: ["Bootstrapped", "Seed", "Series A+"] }),
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
        h(TextField, { label: "Hostel/Hall of Residence Name", value: profile.hostel, onChange: set("hostel") }),
        h(TextField, { label: "Favorite Campus Spot", value: profile.favoriteSpot, onChange: set("favoriteSpot") }),
      ),
      h(BadgeMultiSelect, { label: "Clubs/Societies Joined", options: clubOptions, selected: profile.clubs, onChange: set("clubs") }),
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
      h("p", { className: "max-w-3xl text-sm text-blue-100" }, "Complete the profile once, then manage jobs, mentorship, content, student connects, and startup opportunities from one dashboard."),
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
        h("div", { className: "flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5" },
          h("div", { className: "flex items-center gap-2 text-sm text-slate-500" }, h(CheckCircle2, { size: 17, className: "text-emerald-600" }), `${index + 1} of ${steps.length} sections active`),
          h("div", { className: "flex flex-wrap gap-2" },
            h(SecondaryButton, { icon: ChevronLeft, onClick: () => setActiveStep(steps[Math.max(index - 1, 0)][0]), className: index === 0 ? "opacity-50" : "" }, "Back"),
            index < steps.length - 1
              ? h(PrimaryButton, { icon: ChevronRight, onClick: () => setActiveStep(steps[index + 1][0]) }, "Next")
              : h(PrimaryButton, { icon: Sparkles, onClick: () => onLaunch(profile) }, "Save and Launch Dashboard"),
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
    ["give", "Give Back", HandCoins],
    ["content", "Content Hub", Newspaper],
    ["students", "Student Connects", UsersRound],
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

function Overview({ profile, jobs, feed, connections }) {
  return h("div", { className: "grid gap-5" },
    h("div", { className: "grid gap-4 md:grid-cols-4" },
      h(StatCard, { icon: Award, label: "Skills", value: profile.skills.length }),
      h(StatCard, { icon: BriefcaseBusiness, label: "Job Posts", value: jobs.length }),
      h(StatCard, { icon: Newspaper, label: "Feed Updates", value: feed.length }),
      h(StatCard, { icon: MessageCircle, label: "Connections", value: connections.length }),
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
  );
}

function GiveBackPortal({ profile, jobs, setJobs }) {
  const [jobForm, setJobForm] = useState({ title: "", company: profile.company, type: "Job", location: "", description: "" });
  const [applicants, setApplicants] = useState(seedApplicants);
  const set = (key) => (value) => setJobForm((current) => ({ ...current, [key]: value }));
  const updateApplicant = (id, status) => setApplicants((current) => current.map((item) => item.id === id ? { ...item, status } : item));

  return h("div", { className: "grid gap-5 xl:grid-cols-[0.95fr_1.05fr]" },
    h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100" },
      h("div", { className: "mb-5" }, h("h3", { className: "text-lg font-bold text-slate-900" }, "Post Job or Internship"), h("p", { className: "text-sm text-slate-500" }, "New openings appear instantly on the exclusive job board.")),
      h("form", {
        className: "grid gap-4",
        onSubmit: (event) => {
          event.preventDefault();
          if (!jobForm.title.trim()) return;
          setJobs((current) => [{ ...jobForm, id: Date.now() }, ...current]);
          setJobForm({ title: "", company: profile.company, type: "Job", location: "", description: "" });
        },
      },
        h("div", { className: "grid gap-4 md:grid-cols-2" },
          h(TextField, { label: "Job Title", value: jobForm.title, onChange: set("title") }),
          h(TextField, { label: "Company", value: jobForm.company, onChange: set("company") }),
          h(TextField, { label: "Type", value: jobForm.type, onChange: set("type"), options: ["Job", "Internship", "Remote"] }),
          h(TextField, { label: "Location", value: jobForm.location, onChange: set("location") }),
        ),
        h(TextField, { label: "Description", value: jobForm.description, onChange: set("description"), textarea: true }),
        h(PrimaryButton, { icon: Plus, type: "submit", className: "justify-self-start" }, "Publish Opening"),
      ),
    ),
    h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100" },
      h("div", { className: "mb-4 flex items-center justify-between" }, h("h3", { className: "text-lg font-bold text-slate-900" }, "Exclusive Job Board"), h("span", { className: "rounded-full bg-amber-50 px-3 py-1 text-sm font-bold text-[#F59E0B]" }, `${jobs.length} live`)),
      h("div", { className: "grid gap-3" }, jobs.map((job) =>
        h("article", { key: job.id, className: "rounded-lg border border-slate-100 p-4" },
          h("div", { className: "flex items-start justify-between gap-3" },
            h("div", null, h("h4", { className: "font-bold text-slate-900" }, job.title), h("p", { className: "text-sm text-slate-500" }, `${job.company} - ${job.location || "Flexible"}`)),
            h("span", { className: "rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-[#1E3A8A]" }, job.type),
          ),
          h("p", { className: "mt-3 text-sm text-slate-600" }, job.description),
        ),
      )),
    ),
    h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100 xl:col-span-2" },
      h("div", { className: "mb-4 flex flex-wrap items-center justify-between gap-3" }, h("h3", { className: "text-lg font-bold text-slate-900" }, "Applicant Tracker"), h(IconLabel, { icon: ClipboardCheck, className: "text-sm font-bold text-slate-500" }, "Mock student applicants")),
      h("div", { className: "overflow-x-auto" },
        h("table", { className: "min-w-[720px] w-full border-collapse text-sm" },
          h("thead", null, h("tr", { className: "bg-slate-50 text-left text-xs uppercase text-slate-500" }, ["Student", "Applied For", "Department", "Status", "Actions"].map((head) => h("th", { key: head, className: "px-3 py-3 font-bold" }, head)))),
          h("tbody", null, applicants.map((applicant) =>
            h("tr", { key: applicant.id, className: "border-b border-slate-100" },
              h("td", { className: "px-3 py-3 font-bold text-slate-900" }, applicant.name),
              h("td", { className: "px-3 py-3 text-slate-600" }, applicant.role),
              h("td", { className: "px-3 py-3 text-slate-600" }, applicant.department),
              h("td", { className: "px-3 py-3" }, h("span", { className: "rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-[#B45309]" }, applicant.status)),
              h("td", { className: "px-3 py-3" },
                h("div", { className: "flex flex-wrap gap-2" },
                  h(SecondaryButton, { icon: FileText, onClick: () => updateApplicant(applicant.id, "Resume Reviewed"), className: "px-3 py-2" }, "Review Resume"),
                  h(PrimaryButton, { icon: CalendarClock, onClick: () => updateApplicant(applicant.id, "Interview Invited"), className: "px-3 py-2" }, "Invite"),
                ),
              ),
            ),
          )),
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

function StudentConnects({ connections, setConnections }) {
  const [query, setQuery] = useState("");
  const filtered = studentDirectory.filter((student) => `${student.name} ${student.department} ${student.interests}`.toLowerCase().includes(query.toLowerCase()));
  return h("section", { className: "rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-100" },
    h("div", { className: "mb-5 flex flex-wrap items-center justify-between gap-3" },
      h("div", null, h("h3", { className: "mb-1 text-lg font-bold text-slate-900" }, "Student Interaction & Connects"), h("p", { className: "text-sm text-slate-500" }, "Directory of students currently seeking alumni guidance.")),
      h("label", { className: "relative min-w-[260px]" }, h(Search, { className: "absolute left-3 top-2.5 text-slate-400", size: 17 }), h("input", { value: query, onChange: (event) => setQuery(event.target.value), placeholder: "Search students", className: "w-full rounded-md border border-slate-200 py-2 pl-9 pr-3 text-sm outline-none focus:border-[#F59E0B] focus:ring-2 focus:ring-amber-100" })),
    ),
    h("div", { className: "grid gap-4 lg:grid-cols-2 xl:grid-cols-4" }, filtered.map((student) => {
      const connected = connections.includes(student.id);
      return h("article", { key: student.id, className: "rounded-lg border border-slate-100 p-4" },
        h("div", { className: "mb-4 flex items-center gap-3" },
          h("span", { className: "grid h-11 w-11 place-items-center rounded-full bg-[#1E3A8A] text-sm font-bold text-white" }, student.name.split(" ").map((part) => part[0]).join("")),
          h("div", null, h("h4", { className: "font-bold text-slate-900" }, student.name), h("p", { className: "text-sm text-slate-500" }, student.department)),
        ),
        h("p", { className: "mb-4 min-h-[64px] text-sm text-slate-600" }, student.interests),
        h(connected ? SecondaryButton : PrimaryButton, { icon: connected ? CheckCircle2 : MessageCircle, onClick: () => setConnections((current) => connected ? current : [...current, student.id]), className: "w-full" }, connected ? "Connection Requested" : "Connect / Message"),
      );
    })),
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
          h(TextField, { label: "Full Name", value: profile.fullName, onChange: set("fullName") }),
          h(TextField, { label: "Graduation Batch Year", value: profile.batchYear, onChange: set("batchYear"), type: "number" }),
          h(TextField, { label: "Academic Department", value: profile.department, onChange: set("department") }),
          h(TextField, { label: "Current Company", value: profile.company, onChange: set("company") }),
          h(TextField, { label: "Designation", value: profile.designation, onChange: set("designation") }),
          h(TextField, { label: "Current City/Country", value: profile.cityCountry, onChange: set("cityCountry") }),
        ),
      ),
      h(SetupStepShell, { title: "Expertise", subtitle: "Skills, industry domain, publications, and patents.", icon: Award },
        h(BadgeMultiSelect, { label: "Core Skills/Technologies", options: skillOptions, selected: profile.skills, onChange: set("skills") }),
        h(TextField, { label: "Industry Domain", value: profile.industryDomain, onChange: set("industryDomain"), options: ["EdTech", "FinTech", "Healthcare", "SaaS", "Manufacturing", "Consulting"] }),
        h(TextField, { label: "Patents/Research Publications", value: profile.publications, onChange: set("publications"), textarea: true }),
      ),
      h(SetupStepShell, { title: "Mentorship & Availability", subtitle: "Availability, guidance areas, and weekly hours.", icon: Handshake },
        h(Toggle, { checked: profile.mentorshipAvailable, onChange: set("mentorshipAvailable"), label: "Available for Student Mentorship" }),
        h(BadgeMultiSelect, { label: "Areas of Guidance", options: guidanceOptions, selected: profile.guidanceAreas, onChange: set("guidanceAreas") }),
        h(TextField, { label: "Weekly Availability", value: profile.weeklyAvailability, onChange: set("weeklyAvailability"), options: ["1 Hour/Week", "2 Hours/Week", "Weekends Only", "Monthly Office Hours"] }),
      ),
      h(SetupStepShell, { title: "Startup Profile", subtitle: "Optional founder, hiring, and investment preferences.", icon: Rocket },
        h("div", { className: "grid gap-4 md:grid-cols-2" }, h(TextField, { label: "Startup Name", value: profile.startupName, onChange: set("startupName") }), h(TextField, { label: "Website URL", value: profile.startupWebsite, onChange: set("startupWebsite") }), h(TextField, { label: "Funding Stage", value: profile.fundingStage, onChange: set("fundingStage"), options: ["Bootstrapped", "Seed", "Series A+"] })),
        h(Toggle, { checked: profile.hiringInterns, onChange: set("hiringInterns"), label: "Actively Hiring Interns" }),
        h(Toggle, { checked: profile.angelInvesting, onChange: set("angelInvesting"), label: "Interested in Angel Investing in Student Startups" }),
      ),
      h(SetupStepShell, { title: "College Memories", subtitle: "Hostel, clubs, societies, and favorite campus spot.", icon: BookOpenText },
        h("div", { className: "grid gap-4 md:grid-cols-2" }, h(TextField, { label: "Hostel/Hall of Residence Name", value: profile.hostel, onChange: set("hostel") }), h(TextField, { label: "Favorite Campus Spot", value: profile.favoriteSpot, onChange: set("favoriteSpot") })),
        h(BadgeMultiSelect, { label: "Clubs/Societies Joined", options: clubOptions, selected: profile.clubs, onChange: set("clubs") }),
      ),
    ),
  );
}

function MainDashboard({ profile, setProfile }) {
  const [active, setActive] = useState("overview");
  const [jobs, setJobs] = useState(seedJobs);
  const [feed, setFeed] = useState(seedFeed);
  const [connections, setConnections] = useState([]);

  const view = {
    overview: h(Overview, { profile, jobs, feed, connections }),
    give: h(GiveBackPortal, { profile, jobs, setJobs }),
    content: h(ContentHub, { feed, setFeed }),
    students: h(StudentConnects, { connections, setConnections }),
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
