import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  Bell,
  BadgeCheck,
  CheckCircle2,
  Circle,
  GraduationCap,
  MessageCircle,
  Send,
  UserRoundCheck
} from "lucide-react";
import {
  currentTimestamp,
  mentorConversations,
  mentorMilestones,
  mentors,
  mentorshipUsers,
  readSharedMentorshipThread,
  sharedMentorshipChannelName,
  sharedMentorshipThreadKey,
  studentNotifications,
  writeSharedMentorshipThread
} from "./mentorshipMockData";

const studentQuickReplies = [
  "I have uploaded my latest resume.",
  "Can we schedule a mock interview this week?",
  "I shared my GitHub profile for review."
];

function NotificationMenu({ notifications, open, onToggle, onSelect }) {
  const unreadCount = notifications.filter((item) => item.unread).length;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggle}
        className="relative grid h-11 w-11 place-items-center rounded-md border border-white/20 bg-white/10 text-white transition hover:bg-white/15"
        aria-label="Open notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 grid min-h-5 min-w-5 place-items-center rounded-full bg-gold px-1 text-xs font-bold text-white shadow">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-14 z-30 w-80 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-panel">
          <div className="border-b border-slate-100 px-4 py-3">
            <p className="text-sm font-semibold text-slate-950">Notifications</p>
            <p className="text-xs text-slate-500">Live mentorship activity</p>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.map((item) => (
              <button
                type="button"
                key={item.id}
                onClick={() => onSelect(item)}
                className="flex w-full gap-3 px-4 py-3 text-left transition hover:bg-slate-50"
              >
                <span className="mt-1 h-2.5 w-2.5 rounded-full bg-gold" />
                <span className="min-w-0">
                  <span className="block text-sm font-semibold text-slate-900">{item.title}</span>
                  <span className="block text-sm text-slate-600">{item.body}</span>
                  <span className="mt-1 block text-xs text-slate-400">{item.timestamp}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ProgressPanel({ milestones, mentorName }) {
  const completed = milestones.filter((goal) => goal.completed).length;
  const progress = Math.round((completed / Math.max(milestones.length, 1)) * 100);

  return (
    <aside className="flex min-h-0 flex-col border-l border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-navy text-white">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-950">Mentorship Roadmap</h2>
            <p className="text-sm text-slate-500">Controlled by {mentorName}</p>
          </div>
        </div>
      </div>

      <div className="space-y-6 overflow-y-auto p-5">
        <div>
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-semibold text-slate-700">Journey progress</span>
            <span className="font-bold text-navy">{progress}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-gold transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <div className="space-y-3">
          {milestones.map((goal) => (
            <div key={goal.id} className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
              {goal.completed ? (
                <CheckCircle2 className="mt-0.5 h-5 w-5 flex-none text-gold" />
              ) : (
                <Circle className="mt-0.5 h-5 w-5 flex-none text-slate-300" />
              )}
              <div>
                <p className="text-sm font-semibold text-slate-900">{goal.title}</p>
                <p className="text-xs text-slate-500">Read-only milestone</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

function MentorDirectory({ activeMentorId, mentorList, onSelect }) {
  return (
    <aside className="flex min-h-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-5">
        <h2 className="text-base font-bold text-slate-950">My Mentors</h2>
        <p className="text-sm text-slate-500">Connected alumni directory</p>
      </div>
      <div className="space-y-2 overflow-y-auto p-3">
        {mentorList.map((mentor) => {
          const active = mentor.id === activeMentorId;
          return (
            <button
              type="button"
              key={mentor.id}
              onClick={() => onSelect(mentor.id)}
              className={`w-full rounded-lg border p-4 text-left transition ${
                active ? "border-navy bg-blue-50" : "border-transparent hover:border-slate-200 hover:bg-slate-50"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-bold text-slate-950">{mentor.name}</p>
                    {mentor.certified && <BadgeCheck className="h-4 w-4 flex-none text-gold" />}
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{mentor.company}</p>
                  <p className="mt-2 text-xs font-medium text-slate-500">{mentor.expertise}</p>
                </div>
                {mentor.unread > 0 && <span className="mt-1 h-3 w-3 rounded-full bg-gold shadow" />}
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

function MessageStream({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-scroll flex-1 overflow-y-auto bg-slate-50 p-5">
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        {messages.map((message) => {
          const sentByStudent = message.sender === "student";
          return (
            <div key={message.id} className={`flex ${sentByStudent ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[78%] rounded-lg px-4 py-3 shadow-sm ${
                  sentByStudent ? "bg-navy text-white" : "border border-slate-200 bg-slate-100 text-slate-900"
                }`}
              >
                <p className="text-sm leading-6">{message.text}</p>
                <p className={`mt-2 text-xs ${sentByStudent ? "text-blue-100" : "text-slate-500"}`}>{message.timestamp}</p>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

export default function StudentDashboard() {
  const [activeMentorId, setActiveMentorId] = useState(mentors[0].id);
  const [mentorList, setMentorList] = useState(mentors);
  const [conversations, setConversations] = useState(mentorConversations);
  const [draft, setDraft] = useState("");
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState(studentNotifications);
  const activeMentor = useMemo(
    () => mentorList.find((mentor) => mentor.id === activeMentorId) || mentorList[0],
    [activeMentorId, mentorList]
  );
  const activeMessages = conversations[activeMentorId] || [];
  const activeMilestones = mentorMilestones[activeMentorId] || mentorMilestones[mentors[0].id];

  const selectMentor = (mentorId) => {
    setActiveMentorId(mentorId);
    setMentorList((current) =>
      current.map((mentor) => (mentor.id === mentorId ? { ...mentor, unread: 0, active: true } : mentor))
    );
  };

  useEffect(() => {
    window.history.replaceState({ page: "student-chats" }, "", window.location.href);
    const forceStudentDashboard = () => {
      window.location.replace("http://127.0.0.1:9000/login?role=student");
    };
    window.addEventListener("popstate", forceStudentDashboard);
    setConversations((current) => ({
      ...current,
      "mentor-rohit": readSharedMentorshipThread(current["mentor-rohit"] || [])
    }));

    const syncThread = (event) => {
      if (event.key !== sharedMentorshipThreadKey || !event.newValue) return;
      const nextMessages = readSharedMentorshipThread(mentorConversations["mentor-rohit"]);
      setConversations((current) => ({
        ...current,
        "mentor-rohit": nextMessages
      }));
      if (activeMentorId !== "mentor-rohit") {
        setMentorList((current) =>
          current.map((mentor) => (mentor.id === "mentor-rohit" ? { ...mentor, unread: Math.max(mentor.unread, 1) } : mentor))
        );
      }
    };

    const channel = "BroadcastChannel" in window ? new BroadcastChannel(sharedMentorshipChannelName) : null;
    if (channel) {
      channel.onmessage = (event) => {
        if (!Array.isArray(event.data)) return;
        setConversations((current) => ({
          ...current,
          "mentor-rohit": event.data
        }));
        if (activeMentorId !== "mentor-rohit") {
          setMentorList((current) =>
            current.map((mentor) => (mentor.id === "mentor-rohit" ? { ...mentor, unread: Math.max(mentor.unread, 1) } : mentor))
          );
        }
      };
    }

    window.addEventListener("storage", syncThread);
    return () => {
      window.removeEventListener("storage", syncThread);
      window.removeEventListener("popstate", forceStudentDashboard);
      channel?.close();
    };
  }, [activeMentorId]);

  const sendMessage = (text = draft) => {
    const cleanText = text.trim();
    if (!cleanText) return;
    const nextMessage = {
      id: `student-msg-${Date.now()}`,
      sender: "student",
      text: cleanText,
      timestamp: currentTimestamp()
    };
    setConversations((current) => ({
      ...current,
      [activeMentorId]: (() => {
        const nextMessages = [...(current[activeMentorId] || []), nextMessage];
        if (activeMentorId === "mentor-rohit") writeSharedMentorshipThread(nextMessages);
        return nextMessages;
      })()
    }));
    setDraft("");
  };

  const selectNotification = (item) => {
    setNotifications((current) =>
      current.map((notification) => (notification.id === item.id ? { ...notification, unread: false } : notification))
    );
    setNotificationOpen(false);
    if (item.id === "student-note-2") {
      selectMentor("mentor-rohit");
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <header className="flex h-16 items-center justify-between bg-navy px-5 text-white shadow">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              window.location.replace("http://127.0.0.1:9000/login?role=student");
            }}
            className="grid h-10 w-10 place-items-center rounded-md border border-white/20 bg-white/10 transition hover:bg-white/15"
            aria-label="Back to student dashboard"
            title="Back to student dashboard"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="grid h-10 w-10 place-items-center rounded-md bg-white/10">
            <UserRoundCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold">Chats</h1>
            <p className="text-sm text-blue-100">{mentorshipUsers.student.title}</p>
          </div>
        </div>
        <NotificationMenu
          notifications={notifications}
          open={notificationOpen}
          onToggle={() => setNotificationOpen((open) => !open)}
          onSelect={selectNotification}
        />
      </header>

      <main className="grid h-[calc(100vh-4rem)] grid-cols-1 overflow-hidden lg:grid-cols-[20rem_minmax(0,1fr)_22rem]">
        <MentorDirectory activeMentorId={activeMentorId} mentorList={mentorList} onSelect={selectMentor} />

        <section className="flex min-h-0 flex-col bg-white">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-950">{activeMentor.name}</h2>
                <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-bold text-amber-700">Connected</span>
              </div>
              <p className="text-sm text-slate-500">{activeMentor.company}</p>
            </div>
            <MessageCircle className="h-5 w-5 text-navy" />
          </div>

          <MessageStream messages={activeMessages} />

          <div className="border-t border-slate-200 bg-white p-4">
            <div className="mx-auto max-w-4xl space-y-3">
              <div className="flex flex-wrap gap-2">
                {studentQuickReplies.map((reply) => (
                  <button
                    type="button"
                    key={reply}
                    onClick={() => sendMessage(reply)}
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-gold hover:bg-amber-50 hover:text-amber-700"
                  >
                    {reply}
                  </button>
                ))}
              </div>
              <div className="flex gap-3">
                <input
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") sendMessage();
                  }}
                  placeholder="Type your mentorship message"
                  className="min-w-0 flex-1 rounded-md border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-navy focus:ring-2 focus:ring-blue-100"
                />
                <button
                  type="button"
                  onClick={() => sendMessage()}
                  className="inline-flex items-center gap-2 rounded-md bg-gold px-5 py-3 text-sm font-bold text-white transition hover:bg-amber-600"
                >
                  <Send className="h-4 w-4" />
                  Send Message
                </button>
              </div>
            </div>
          </div>
        </section>

        <ProgressPanel milestones={activeMilestones} mentorName={activeMentor.name} />
      </main>
    </div>
  );
}
