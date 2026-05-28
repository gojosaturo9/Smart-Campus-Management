import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import AlumniDashboard from "./AlumniDashboard.jsx";
import StudentDashboard from "./StudentDashboard.jsx";
import {
  ArrowLeft,
  Award,
  BadgeCheck,
  CalendarDays,
  Check,
  ChevronRight,
  Clock3,
  FileText,
  Goal,
  GraduationCap,
  Link as LinkIcon,
  MessageCircle,
  Mic,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Star,
  UserCheck,
  Video,
  X
} from "lucide-react";
import "./styles.css";

const ROLES = {
  alumni: {
    label: "Alumni Chat View",
    name: "Ananya Rao",
    title: "Senior SDE Alumni Mentor",
    peerLabel: "Mentees"
  },
  student: {
    label: "Student Chat View",
    name: "Sagar Senapati",
    title: "Final Year CSE Student",
    peerLabel: "Mentors"
  }
};

const initialRequests = [
  {
    id: "req-1",
    student: "Sagar Senapati",
    avatar: "SS",
    intent: "Resume Review",
    message: "I am applying for backend roles and need a certified resume review before placements.",
    stack: ["React", "FastAPI", "SQL"],
    match: 95
  },
  {
    id: "req-2",
    student: "Meera Iyer",
    avatar: "MI",
    intent: "Mock Interview",
    message: "Can we do one system design mock interview this week?",
    stack: ["Java", "DSA", "AWS"],
    match: 91
  }
];

const initialMatches = [
  {
    id: "match-1",
    name: "Ananya Rao",
    avatar: "AR",
    title: "Senior SDE, Product Engineering",
    stack: ["React", "FastAPI", "SQL"],
    match: 95,
    online: true
  },
  {
    id: "match-2",
    name: "Rohit Menon",
    avatar: "RM",
    title: "Data Platform Engineer",
    stack: ["Python", "Spark", "Cloud"],
    match: 88,
    online: false
  }
];

const initialChats = [
  {
    id: "chat-1",
    studentName: "Sagar Senapati",
    alumniName: "Ananya Rao",
    avatar: "SS",
    online: true,
    certified: true,
    unread: 2,
    lastMessage: "I uploaded my resume draft.",
    intent: "Resume Review"
  }
];

const initialMessages = [
  {
    id: "m-1",
    chatId: "chat-1",
    sender: "student",
    text: "Hello ma'am, I need help preparing for backend placement interviews.",
    time: "10:12 AM"
  },
  {
    id: "m-2",
    chatId: "chat-1",
    sender: "alumni",
    text: "Sure. Send your latest resume and GitHub link. I will review the project framing first.",
    time: "10:14 AM"
  },
  {
    id: "m-3",
    chatId: "chat-1",
    sender: "student",
    text: "Sharing both here. I want feedback on impact points and ATS readability.",
    time: "10:16 AM",
    attachment: {
      type: "resume",
      title: "Sagar_Senapati_Backend_Resume.pdf",
      score: 78
    }
  },
  {
    id: "m-4",
    chatId: "chat-1",
    sender: "alumni",
    text: "I have added the first review markers. Let us also schedule a mock interview.",
    time: "10:22 AM",
    attachment: {
      type: "schedule",
      title: "Backend Mock Interview",
      slot: "Friday, 6:30 PM",
      status: "pending"
    }
  }
];

const initialGoals = [
  { id: "g-1", title: "Complete Resume Draft", due: "Today", done: true },
  { id: "g-2", title: "Add GitHub project README metrics", due: "Tomorrow", done: false },
  { id: "g-3", title: "Solve 50 DSA Array Problems", due: "7 days", done: false },
  { id: "g-4", title: "Attend Mock Interview 1", due: "Friday", done: false }
];

const quickReplies = {
  alumni: [
    "Sure, send over your resume!",
    "Let's set up a mock interview.",
    "Can you share your GitHub link?"
  ],
  student: [
    "I have updated the resume draft.",
    "I accept the meeting invite.",
    "Can you review my project summary?"
  ]
};

function nowTime() {
  return new Intl.DateTimeFormat("en-IN", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true
  }).format(new Date());
}

function App() {
  const [role, setRole] = useState(() => {
    const queryRole = new URLSearchParams(window.location.search).get("role");
    return queryRole === "student" ? "student" : "alumni";
  });
  const [activeTab, setActiveTab] = useState("requests");
  const [requests, setRequests] = useState(initialRequests);
  const [matches, setMatches] = useState(initialMatches);
  const [chats, setChats] = useState(initialChats);
  const [activeChatId, setActiveChatId] = useState("chat-1");
  const [messages, setMessages] = useState(initialMessages);
  const [goals, setGoals] = useState(initialGoals);
  const [draft, setDraft] = useState("");
  const [reviewOpen, setReviewOpen] = useState(false);
  const [feedback, setFeedback] = useState([
    "Move FastAPI attendance platform into the top project slot.",
    "Add numbers for users, latency, or automation impact.",
    "Convert responsibilities into accomplishment bullets."
  ]);
  const [newFeedback, setNewFeedback] = useState("");
  const [newGoal, setNewGoal] = useState("");
  const [certificateOpen, setCertificateOpen] = useState(false);

  const activeChat = chats.find((chat) => chat.id === activeChatId) || chats[0];
  const visibleMessages = messages.filter((message) => message.chatId === activeChat?.id);
  const completedGoals = goals.filter((goalItem) => goalItem.done).length;
  const progress = Math.round((completedGoals / Math.max(goals.length, 1)) * 100);

  useEffect(() => {
    if (activeChatId) {
      setChats((current) =>
        current.map((chat) => (chat.id === activeChatId ? { ...chat, unread: 0 } : chat))
      );
    }
  }, [activeChatId]);

  const sendMessage = (text, attachment) => {
    const clean = text.trim();
    if (!clean && !attachment) return;
    const message = {
      id: `m-${Date.now()}`,
      chatId: activeChat.id,
      sender: role,
      text: clean,
      time: nowTime(),
      attachment
    };
    setMessages((current) => [...current, message]);
    setChats((current) =>
      current.map((chat) =>
        chat.id === activeChat.id
          ? { ...chat, lastMessage: clean || attachment?.title || "Shared an update" }
          : chat
      )
    );
    setDraft("");
  };

  const acceptConnect = (request) => {
    const chatId = `chat-${Date.now()}`;
    setChats((current) => [
      {
        id: chatId,
        studentName: request.student,
        alumniName: "Ananya Rao",
        avatar: request.avatar,
        online: true,
        certified: true,
        unread: 1,
        lastMessage: request.message,
        intent: request.intent
      },
      ...current
    ]);
    setMessages((current) => [
      ...current,
      {
        id: `m-${Date.now()}`,
        chatId,
        sender: "student",
        text: request.message,
        time: nowTime()
      }
    ]);
    setRequests((current) => current.filter((item) => item.id !== request.id));
    setActiveChatId(chatId);
    setActiveTab("chats");
  };

  const connectMatch = (match) => {
    const chatId = `chat-${Date.now()}`;
    setChats((current) => [
      {
        id: chatId,
        studentName: "Sagar Senapati",
        alumniName: match.name,
        avatar: match.avatar,
        online: match.online,
        certified: true,
        unread: 0,
        lastMessage: "Connection request accepted.",
        intent: "Placement Advice"
      },
      ...current
    ]);
    setMessages((current) => [
      ...current,
      {
        id: `m-${Date.now()}`,
        chatId,
        sender: "student",
        text: "Hello, I would like guidance for placement preparation and project positioning.",
        time: nowTime()
      }
    ]);
    setMatches((current) => current.filter((item) => item.id !== match.id));
    setActiveChatId(chatId);
    setActiveTab("chats");
  };

  const addGoal = () => {
    if (!newGoal.trim()) return;
    setGoals((current) => [
      ...current,
      { id: `g-${Date.now()}`, title: newGoal.trim(), due: "Timed Goal", done: false }
    ]);
    setNewGoal("");
  };

  const addFeedback = () => {
    if (!newFeedback.trim()) return;
    setFeedback((current) => [...current, newFeedback.trim()]);
    setNewFeedback("");
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <TopBar role={role} setRole={setRole} />
      <main className="mx-auto flex h-[calc(100vh-88px)] max-w-[1540px] gap-4 px-4 pb-4 pt-4">
        <LeftPanel
          role={role}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          requests={requests}
          matches={matches}
          chats={chats}
          activeChatId={activeChatId}
          setActiveChatId={setActiveChatId}
          acceptConnect={acceptConnect}
          declineConnect={(id) => setRequests((current) => current.filter((item) => item.id !== id))}
          connectMatch={connectMatch}
        />
        <ChatCanvas
          role={role}
          activeChat={activeChat}
          messages={visibleMessages}
          draft={draft}
          setDraft={setDraft}
          sendMessage={sendMessage}
          setReviewOpen={setReviewOpen}
        />
        <GoalSidebar
          role={role}
          goals={goals}
          setGoals={setGoals}
          newGoal={newGoal}
          setNewGoal={setNewGoal}
          addGoal={addGoal}
          progress={progress}
          setCertificateOpen={setCertificateOpen}
        />
      </main>
      {reviewOpen && (
        <ResumeReviewOverlay
          feedback={feedback}
          newFeedback={newFeedback}
          setNewFeedback={setNewFeedback}
          addFeedback={addFeedback}
          close={() => setReviewOpen(false)}
        />
      )}
      {certificateOpen && <CertificateModal close={() => setCertificateOpen(false)} />}
    </div>
  );
}

function TopBar({ role, setRole }) {
  const backUrl = new URLSearchParams(window.location.search).get("back") || "http://127.0.0.1:9001/alumni/dashboard";

  return (
    <header className="flex h-[88px] items-center justify-between border-b border-slate-200 bg-white/95 px-5 shadow-sm backdrop-blur">
      <div className="flex items-center gap-3">
        <button
          className="grid h-11 w-11 place-items-center rounded-xl border border-slate-200 bg-white text-navy transition hover:border-gold hover:bg-amber-50 hover:text-gold"
          title="Back to alumni dashboard"
          onClick={() => {
            window.location.href = backUrl;
          }}
        >
          <ArrowLeft size={21} />
        </button>
        <div className="grid h-12 w-12 place-items-center rounded-xl bg-navy text-white shadow-panel ring-4 ring-blue-50">
          <GraduationCap size={24} />
        </div>
        <div>
          <h1 className="text-xl font-black text-navy">Certified Mentorship Workspace</h1>
          <p className="text-sm font-medium text-slate-500">Student-alumni guidance, goals, reviews, and meeting flow</p>
        </div>
      </div>
      <div className="flex rounded-2xl border border-slate-200 bg-slate-100 p-1.5 shadow-inner">
        {Object.entries(ROLES).map(([key, value]) => (
          <button
            key={key}
            className={`rounded-xl px-4 py-2.5 text-sm font-bold transition ${
              role === key ? "bg-navy text-white shadow-md" : "text-slate-600 hover:bg-white hover:text-navy"
            }`}
            onClick={() => setRole(key)}
          >
            {value.label}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-gold text-white">
          <ShieldCheck size={19} />
        </span>
        <div>
          <p className="text-sm font-bold text-navy">{ROLES[role].name}</p>
          <p className="text-xs font-semibold text-amber-700">{ROLES[role].title}</p>
        </div>
      </div>
    </header>
  );
}

function LeftPanel(props) {
  const {
    role,
    activeTab,
    setActiveTab,
    requests,
    matches,
    chats,
    activeChatId,
    setActiveChatId,
    acceptConnect,
    declineConnect,
    connectMatch
  } = props;

  return (
    <aside className="w-[320px] shrink-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-panel">
      <div className="border-b border-slate-200 p-4">
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
          <Search size={17} className="text-slate-400" />
          <input className="w-full bg-transparent text-sm outline-none" placeholder="Search people or intent" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <TabButton active={activeTab === "requests"} onClick={() => setActiveTab("requests")}>
            {role === "alumni" ? "Requests" : "Matches"}
          </TabButton>
          <TabButton active={activeTab === "chats"} onClick={() => setActiveTab("chats")}>
            Active Chats
          </TabButton>
        </div>
      </div>
      <div className="h-[calc(100%-118px)] overflow-y-auto p-3">
        {activeTab === "requests" && role === "alumni" && (
          <div className="space-y-3">
            {requests.map((request) => (
              <RequestCard
                key={request.id}
                request={request}
                accept={() => acceptConnect(request)}
                decline={() => declineConnect(request.id)}
              />
            ))}
            {!requests.length && <EmptyState text="No new incoming requests." />}
          </div>
        )}
        {activeTab === "requests" && role === "student" && (
          <div className="space-y-3">
            {matches.map((match) => (
              <MatchCard key={match.id} match={match} connect={() => connectMatch(match)} />
            ))}
            {!matches.length && <EmptyState text="All recommended matches are now in active chats." />}
          </div>
        )}
        {activeTab === "chats" && (
          <div className="space-y-2">
            {chats.map((chat) => (
              <ChatListItem
                key={chat.id}
                chat={chat}
                role={role}
                active={chat.id === activeChatId}
                onClick={() => setActiveChatId(chat.id)}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      className={`rounded-lg px-3 py-2 text-sm font-bold transition ${
        active ? "bg-gold text-white" : "bg-white text-slate-600 hover:bg-slate-100"
      }`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function RequestCard({ request, accept, decline }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-3 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start gap-3">
        <Avatar initials={request.avatar} />
        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-navy">{request.student}</h3>
          <p className="mt-1 inline-flex rounded-full bg-amber-100 px-2 py-1 text-xs font-bold text-amber-700">
            {request.intent}
          </p>
          <p className="mt-2 text-sm leading-5 text-slate-600">{request.message}</p>
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        <button className="flex-1 rounded-lg bg-navy px-3 py-2 text-sm font-bold text-white transition hover:bg-blue-900" onClick={accept}>
          Accept Connect
        </button>
        <button className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-50" onClick={decline}>
          Decline
        </button>
      </div>
    </article>
  );
}

function MatchCard({ match, connect }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-3 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start gap-3">
        <Avatar initials={match.avatar} />
        <div className="min-w-0">
          <h3 className="font-bold text-navy">{match.name}</h3>
          <p className="text-sm text-slate-500">{match.title}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {match.stack.map((item) => (
              <span key={item} className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between rounded-lg bg-amber-50 px-3 py-2">
        <span className="flex items-center gap-1 text-sm font-bold text-amber-700">
          <BadgeCheck size={16} /> {match.match}% Skill Match
        </span>
        <button className="rounded-md bg-gold px-3 py-1.5 text-xs font-bold text-white" onClick={connect}>
          Connect
        </button>
      </div>
    </article>
  );
}

function ChatListItem({ chat, role, active, onClick }) {
  const name = role === "alumni" ? chat.studentName : chat.alumniName;
  return (
    <button
      className={`w-full rounded-xl border p-3 text-left transition ${
        active ? "border-gold bg-amber-50" : "border-transparent hover:bg-slate-50"
      }`}
      onClick={onClick}
    >
      <div className="flex items-center gap-3">
        <div className="relative">
          <Avatar initials={chat.avatar} />
          {chat.online && <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate font-bold text-navy">{name}</p>
            {chat.certified && <BadgeCheck className="shrink-0 text-gold" size={16} />}
          </div>
          <p className="truncate text-sm text-slate-500">{chat.lastMessage}</p>
        </div>
        {chat.unread > 0 && (
          <span className="rounded-full bg-gold px-2 py-1 text-xs font-bold text-white">{chat.unread}</span>
        )}
      </div>
    </button>
  );
}

function ChatCanvas({ role, activeChat, messages, draft, setDraft, sendMessage, setReviewOpen }) {
  const endRef = useRef(null);
  const peerName = role === "alumni" ? activeChat?.studentName : activeChat?.alumniName;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const proposeMeeting = () => {
    sendMessage("I am proposing a certified mentoring session for the next interview milestone.", {
      type: "schedule",
      title: "Certified Mentorship Session",
      slot: "Friday, 6:30 PM",
      status: "pending"
    });
  };

  return (
    <section className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div className="flex items-center gap-3">
          <Avatar initials={activeChat?.avatar || "AS"} />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-navy">{peerName}</h2>
              <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-bold text-emerald-700">Online</span>
              <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-bold text-amber-700">Certified Connection</span>
            </div>
            <p className="text-sm text-slate-500">{activeChat?.intent} mentorship thread</p>
          </div>
        </div>
        <div className="flex gap-2">
          <IconButton title="Video session"><Video size={18} /></IconButton>
          <IconButton title="Voice note"><Mic size={18} /></IconButton>
          <button
            className="flex items-center gap-2 rounded-xl bg-gold px-3.5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-amber-600"
            onClick={proposeMeeting}
          >
            <CalendarDays size={17} /> Propose Time
          </button>
        </div>
      </div>
      <div className="chat-scroll flex-1 space-y-4 overflow-y-auto bg-slate-50 px-5 py-5">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} mine={message.sender === role} setReviewOpen={setReviewOpen} />
        ))}
        <div ref={endRef} />
      </div>
      <div className="border-t border-slate-200 bg-white p-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {quickReplies[role].map((reply) => (
            <button
              key={reply}
              className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-sm font-semibold text-amber-700 transition hover:border-gold hover:bg-amber-100"
              onClick={() => sendMessage(reply)}
            >
              {reply}
            </button>
          ))}
        </div>
        <div className="flex items-end gap-3 rounded-xl border border-slate-200 bg-slate-50 p-2">
          <textarea
            className="max-h-28 min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none"
            placeholder="Write a secure mentorship message..."
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage(draft);
              }
            }}
          />
          <button
            className="grid h-11 w-11 place-items-center rounded-lg bg-navy text-white transition hover:bg-blue-900"
            onClick={() => sendMessage(draft)}
            title="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </section>
  );
}

function MessageBubble({ message, mine, setReviewOpen }) {
  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[72%] rounded-2xl px-4 py-3 shadow-sm ${mine ? "bg-navy text-white" : "border border-slate-200 bg-white text-slate-800"}`}>
        {message.text && <p className="text-sm leading-6">{message.text}</p>}
        {message.attachment?.type === "resume" && <ResumeCard attachment={message.attachment} setReviewOpen={setReviewOpen} />}
        {message.attachment?.type === "schedule" && <ScheduleCard attachment={message.attachment} />}
        <p className={`mt-2 text-right text-[11px] ${mine ? "text-blue-100" : "text-slate-400"}`}>{message.time}</p>
      </div>
    </div>
  );
}

function ResumeCard({ attachment, setReviewOpen }) {
  return (
    <button
      className="mt-3 w-full rounded-xl border border-slate-200 bg-white p-3 text-left text-slate-900 transition hover:border-gold hover:shadow-md"
      onClick={() => setReviewOpen(true)}
    >
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-lg bg-blue-50 text-navy">
          <FileText size={22} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-bold text-navy">{attachment.title}</p>
          <p className="text-xs text-slate-500">Click to open inline review overlay</p>
        </div>
        <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-bold text-amber-700">ATS {attachment.score}</span>
      </div>
    </button>
  );
}

function ScheduleCard({ attachment }) {
  const [status, setStatus] = useState(attachment.status || "pending");
  return (
    <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-slate-900">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-lg bg-gold text-white">
          <CalendarDays size={22} />
        </div>
        <div className="flex-1">
          <p className="font-bold text-navy">{attachment.title}</p>
          <p className="flex items-center gap-1 text-sm text-slate-600">
            <Clock3 size={14} /> {attachment.slot}
          </p>
        </div>
      </div>
      {status === "pending" ? (
        <div className="mt-3 flex gap-2">
          <button className="rounded-lg bg-navy px-3 py-2 text-sm font-bold text-white" onClick={() => setStatus("accepted")}>
            Accept Meeting
          </button>
          <button className="rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm font-bold text-amber-700" onClick={() => setStatus("reschedule")}>
            Reschedule
          </button>
        </div>
      ) : (
        <p className="mt-3 rounded-lg bg-white px-3 py-2 text-sm font-bold text-emerald-700">
          {status === "accepted" ? "Meeting accepted and added to mentorship roadmap." : "Reschedule request sent."}
        </p>
      )}
    </div>
  );
}

function GoalSidebar({ role, goals, setGoals, newGoal, setNewGoal, addGoal, progress, setCertificateOpen }) {
  return (
    <aside className="w-[340px] shrink-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-panel">
      <div className="border-b border-slate-200 p-4">
        <div className="flex items-center gap-2">
          <Goal className="text-gold" size={22} />
          <div>
            <h2 className="font-bold text-navy">Certified Goals Tracker</h2>
            <p className="text-sm text-slate-500">Shared milestone roadmap</p>
          </div>
        </div>
        <div className="mt-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-bold text-slate-600">Mentorship Progress</span>
            <span className="font-bold text-gold">{progress}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-gold transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>
      <div className="chat-scroll h-[calc(100%-167px)] overflow-y-auto p-4">
        <div className="space-y-3">
          {goals.map((goalItem) => (
            <label key={goalItem.id} className="flex cursor-pointer gap-3 rounded-xl border border-slate-200 p-3 transition hover:border-gold hover:bg-amber-50">
              <input
                type="checkbox"
                className="mt-1 h-5 w-5 accent-amber-500"
                checked={goalItem.done}
                onChange={() =>
                  setGoals((current) =>
                    current.map((item) => (item.id === goalItem.id ? { ...item, done: !item.done } : item))
                  )
                }
              />
              <span className="min-w-0">
                <span className={`block font-bold ${goalItem.done ? "text-slate-400 line-through" : "text-navy"}`}>{goalItem.title}</span>
                <span className="text-sm text-slate-500">Due: {goalItem.due}</span>
              </span>
            </label>
          ))}
        </div>
        {role === "alumni" && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="mb-2 text-sm font-bold text-navy">Add timed student goal</p>
            <div className="flex gap-2">
              <input
                className="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-gold"
                placeholder="e.g. Attend Mock Interview 1"
                value={newGoal}
                onChange={(event) => setNewGoal(event.target.value)}
              />
              <button className="grid h-10 w-10 place-items-center rounded-lg bg-gold text-white" onClick={addGoal} title="Add goal">
                <Plus size={18} />
              </button>
            </div>
          </div>
        )}
        {progress === 100 && (
          <button
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gold px-4 py-3 font-bold text-white shadow-lg transition hover:bg-amber-600"
            onClick={() => setCertificateOpen(true)}
          >
            <Award size={19} /> Generate Certificate
          </button>
        )}
      </div>
    </aside>
  );
}

function ResumeReviewOverlay({ feedback, newFeedback, setNewFeedback, addFeedback, close }) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-sm">
      <aside className="h-full w-[460px] overflow-y-auto bg-white p-5 shadow-panel">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-navy">Inline Resume Review</h2>
            <p className="text-sm text-slate-500">Certified alumnus feedback markers</p>
          </div>
          <IconButton title="Close" onClick={close}><X size={18} /></IconButton>
        </div>
        <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="rounded-lg bg-white p-4 shadow-sm">
            <p className="text-sm font-bold text-navy">Sagar Senapati</p>
            <p className="text-xs text-slate-500">Backend Developer Resume Preview</p>
            <div className="mt-4 space-y-2">
              {["Smart Campus Platform", "Face Attendance Automation", "FastAPI Module Integration"].map((item) => (
                <div key={item} className="rounded-lg border border-slate-200 p-3">
                  <p className="font-semibold text-slate-700">{item}</p>
                  <div className="mt-2 h-2 w-4/5 rounded-full bg-slate-200" />
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="mt-5 space-y-3">
          {feedback.map((item, index) => (
            <div key={item} className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-gold text-sm font-bold text-white">{index + 1}</span>
              <p className="text-sm leading-6 text-slate-700">{item}</p>
            </div>
          ))}
        </div>
        <div className="mt-5 rounded-xl border border-slate-200 p-3">
          <textarea
            className="min-h-[92px] w-full resize-none text-sm outline-none"
            placeholder="Type another inline feedback point..."
            value={newFeedback}
            onChange={(event) => setNewFeedback(event.target.value)}
          />
          <button className="mt-3 w-full rounded-lg bg-navy px-4 py-2 font-bold text-white" onClick={addFeedback}>
            Add Feedback Point
          </button>
        </div>
      </aside>
    </div>
  );
}

function CertificateModal({ close }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 text-center shadow-panel">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-amber-100 text-gold">
          <Award size={34} />
        </div>
        <h2 className="mt-4 text-2xl font-bold text-navy">Certified Achievement Unlocked</h2>
        <p className="mt-2 text-slate-600">
          Mentorship milestones are complete. The student can generate a certificate and request a LinkedIn endorsement from the alumnus.
        </p>
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="font-bold text-navy">Mentorship Completion Certificate</p>
          <p className="text-sm text-slate-600">Resume Review, Placement Prep, Mock Interview Readiness</p>
        </div>
        <button className="mt-5 rounded-lg bg-gold px-5 py-3 font-bold text-white transition hover:bg-amber-600" onClick={close}>
          Continue
        </button>
      </div>
    </div>
  );
}

function EmptyState({ text }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
      <Sparkles className="mx-auto mb-2 text-gold" size={22} />
      {text}
    </div>
  );
}

function Avatar({ initials }) {
  return <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-navy font-bold text-white">{initials}</div>;
}

function IconButton({ title, onClick, children }) {
  return (
    <button
      className="grid h-10 w-10 place-items-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:border-gold hover:text-gold"
      title={title}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function Root() {
  const params = new URLSearchParams(window.location.search);
  const dashboard = params.get("dashboard");
  const role = params.get("role");

  if (dashboard === "alumni" || role === "alumni") {
    return <AlumniDashboard />;
  }

  return <StudentDashboard />;
}

createRoot(document.getElementById("root")).render(<Root />);
