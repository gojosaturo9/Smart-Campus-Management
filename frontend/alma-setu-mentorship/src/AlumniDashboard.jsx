import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BadgeCheck,
  Bell,
  CheckCircle2,
  Circle,
  ClipboardList,
  MessageCircle,
  Plus,
  Send,
  ShieldCheck,
  UserPlus
} from "lucide-react";
import {
  alumniNotifications,
  currentTimestamp,
  initialMilestones,
  menteeConversations,
  menteeMilestones,
  mentees,
  mentorshipRequests,
  mentorshipUsers,
  quickActionResponses,
  readSharedMentorshipThread,
  sharedMentorshipChannelName,
  sharedMentorshipThreadKey,
  writeSharedMentorshipThread
} from "./mentorshipMockData";

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
            <p className="text-xs text-slate-500">Incoming mentorship activity</p>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.map((item) => (
              <button
                type="button"
                key={item.id}
                onClick={() => onSelect(item)}
                className="flex w-full gap-3 px-4 py-3 text-left transition hover:bg-slate-50"
              >
                <span className={`mt-1 h-2.5 w-2.5 rounded-full ${item.unread ? "bg-gold" : "bg-slate-300"}`} />
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

function PipelineSidebar({ activeTab, setActiveTab, requests, onAccept, activeMentees, activeMenteeId, setActiveMenteeId }) {
  return (
    <aside className="flex min-h-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-5">
        <h2 className="text-base font-bold text-slate-950">Mentorship Pipeline</h2>
        <p className="text-sm text-slate-500">Requests and certified mentees</p>
        <div className="mt-4 grid grid-cols-2 rounded-md bg-slate-100 p-1">
          {[
            ["requests", "Requests"],
            ["mentees", "Mentees"]
          ].map(([key, label]) => (
            <button
              type="button"
              key={key}
              onClick={() => setActiveTab(key)}
              className={`rounded px-3 py-2 text-sm font-semibold transition ${
                activeTab === key ? "bg-white text-navy shadow-sm" : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="chat-scroll min-h-0 flex-1 overflow-y-auto p-3">
        {activeTab === "requests" ? (
          <div className="space-y-3">
            {requests.map((request) => (
              <article key={request.id} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-slate-950">{request.studentName}</p>
                    <p className="text-xs text-slate-500">{request.course}</p>
                  </div>
                  <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-bold text-amber-700">{request.intentTag}</span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-700">{request.message}</p>
                <button
                  type="button"
                  onClick={() => onAccept(request)}
                  className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-gold px-4 py-2.5 text-sm font-bold text-white transition hover:bg-amber-600"
                >
                  <UserPlus className="h-4 w-4" />
                  Accept & Connect
                </button>
              </article>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {activeMentees.map((mentee) => {
              const active = mentee.id === activeMenteeId;
              return (
                <button
                  type="button"
                  key={mentee.id}
                  onClick={() => setActiveMenteeId(mentee.id)}
                  className={`w-full rounded-lg border p-4 text-left transition ${
                    active ? "border-navy bg-blue-50" : "border-transparent hover:border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="truncate text-sm font-bold text-slate-950">{mentee.name}</p>
                        {mentee.certified && <BadgeCheck className="h-4 w-4 flex-none text-gold" />}
                      </div>
                      <p className="mt-1 text-sm text-slate-600">{mentee.intent}</p>
                      <p className="mt-2 text-xs text-slate-500">{mentee.course}</p>
                    </div>
                    <span className={`mt-1 h-3 w-3 rounded-full ${mentee.online ? "bg-emerald-500" : "bg-slate-300"}`} />
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}

function MessageStream({ messages }) {
  return (
    <div className="chat-scroll flex-1 overflow-y-auto bg-slate-50 p-5">
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        {messages.map((message) => {
          const sentByAlumni = message.sender === "alumni";
          return (
            <div key={message.id} className={`flex ${sentByAlumni ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[78%] rounded-lg px-4 py-3 shadow-sm ${
                  sentByAlumni ? "bg-navy text-white" : "border border-slate-200 bg-slate-100 text-slate-900"
                }`}
              >
                <p className="text-sm leading-6">{message.text}</p>
                <p className={`mt-2 text-xs ${sentByAlumni ? "text-blue-100" : "text-slate-500"}`}>{message.timestamp}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RoadmapControlPanel({ milestones, setMilestones }) {
  const [newGoal, setNewGoal] = useState("");
  const completed = milestones.filter((goal) => goal.completed).length;
  const progress = Math.round((completed / Math.max(milestones.length, 1)) * 100);

  const addGoal = () => {
    const cleanTitle = newGoal.trim();
    if (!cleanTitle) return;
    setMilestones((current) => [
      ...current,
      {
        id: `goal-${Date.now()}`,
        title: cleanTitle,
        completed: false,
        controlledBy: "alumni"
      }
    ]);
    setNewGoal("");
  };

  const toggleGoal = (goalId) => {
    setMilestones((current) =>
      current.map((goal) => (goal.id === goalId ? { ...goal, completed: !goal.completed } : goal))
    );
  };

  return (
    <aside className="flex min-h-0 flex-col border-l border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-navy text-white">
            <ClipboardList className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-950">Mentorship Control</h2>
            <p className="text-sm text-slate-500">Milestone roadmap creator</p>
          </div>
        </div>
      </div>

      <div className="chat-scroll min-h-0 flex-1 space-y-5 overflow-y-auto p-5">
        <div>
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-semibold text-slate-700">Student progress</span>
            <span className="font-bold text-navy">{progress}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-gold transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <div className="flex gap-2">
          <input
            value={newGoal}
            onChange={(event) => setNewGoal(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") addGoal();
            }}
            placeholder="Add student goal"
            className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-navy focus:ring-2 focus:ring-blue-100"
          />
          <button
            type="button"
            onClick={addGoal}
            className="grid h-11 w-11 place-items-center rounded-md bg-gold text-white transition hover:bg-amber-600"
            aria-label="Add milestone"
          >
            <Plus className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-3">
          {milestones.map((goal) => (
            <button
              type="button"
              key={goal.id}
              onClick={() => toggleGoal(goal.id)}
              className="flex w-full items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-left transition hover:border-navy/30 hover:bg-blue-50"
            >
              {goal.completed ? (
                <CheckCircle2 className="mt-0.5 h-5 w-5 flex-none text-gold" />
              ) : (
                <Circle className="mt-0.5 h-5 w-5 flex-none text-slate-300" />
              )}
              <span>
                <span className="block text-sm font-semibold text-slate-900">{goal.title}</span>
                <span className="text-xs text-slate-500">Click to update milestone status</span>
              </span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}

export default function AlumniDashboard() {
  const [activeTab, setActiveTab] = useState("requests");
  const [requests, setRequests] = useState(mentorshipRequests);
  const [activeMentees, setActiveMentees] = useState(mentees);
  const [activeMenteeId, setActiveMenteeId] = useState(mentees[0].id);
  const [conversations, setConversations] = useState(menteeConversations);
  const [draft, setDraft] = useState("");
  const [roadmaps, setRoadmaps] = useState(menteeMilestones);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [notifications, setNotifications] = useState(alumniNotifications);
  const backUrl = new URLSearchParams(window.location.search).get("back") || "http://127.0.0.1:9000/login?role=alumni";
  const activeMentee = useMemo(
    () => activeMentees.find((mentee) => mentee.id === activeMenteeId) || activeMentees[0],
    [activeMenteeId, activeMentees]
  );
  const activeMessages = conversations[activeMenteeId] || [];
  const activeMilestones = roadmaps[activeMenteeId] || initialMilestones;

  const updateActiveMilestones = (updater) => {
    setRoadmaps((current) => ({
      ...current,
      [activeMenteeId]: typeof updater === "function" ? updater(current[activeMenteeId] || []) : updater
    }));
  };

  useEffect(() => {
    setConversations((current) => ({
      ...current,
      "mentee-sagar": readSharedMentorshipThread(current["mentee-sagar"] || [])
    }));

    const syncThread = (event) => {
      if (event.key !== sharedMentorshipThreadKey || !event.newValue) return;
      const nextMessages = readSharedMentorshipThread(menteeConversations["mentee-sagar"]);
      setConversations((current) => ({
        ...current,
        "mentee-sagar": nextMessages
      }));
      if (activeMenteeId !== "mentee-sagar") {
        setActiveMentees((current) =>
          current.map((mentee) => (mentee.id === "mentee-sagar" ? { ...mentee, unread: Math.max(mentee.unread, 1) } : mentee))
        );
      }
    };

    const channel = "BroadcastChannel" in window ? new BroadcastChannel(sharedMentorshipChannelName) : null;
    if (channel) {
      channel.onmessage = (event) => {
        if (!Array.isArray(event.data)) return;
        setConversations((current) => ({
          ...current,
          "mentee-sagar": event.data
        }));
        if (activeMenteeId !== "mentee-sagar") {
          setActiveMentees((current) =>
            current.map((mentee) => (mentee.id === "mentee-sagar" ? { ...mentee, unread: Math.max(mentee.unread, 1) } : mentee))
          );
        }
      };
    }

    window.addEventListener("storage", syncThread);
    return () => {
      window.removeEventListener("storage", syncThread);
      channel?.close();
    };
  }, [activeMenteeId]);

  const sendMessage = (text = draft) => {
    const cleanText = text.trim();
    if (!cleanText) return;
    const nextMessage = {
      id: `alumni-msg-${Date.now()}`,
      sender: "alumni",
      text: cleanText,
      timestamp: currentTimestamp()
    };
    setConversations((current) => ({
      ...current,
      [activeMenteeId]: (() => {
        const nextMessages = [...(current[activeMenteeId] || []), nextMessage];
        if (activeMenteeId === "mentee-sagar") writeSharedMentorshipThread(nextMessages);
        return nextMessages;
      })()
    }));
    setDraft("");
  };

  const acceptRequest = (request) => {
    const menteeId = `mentee-${request.studentId}`;
    setRequests((current) => current.filter((item) => item.id !== request.id));
    setActiveMentees((current) => [
      {
        id: menteeId,
        name: request.studentName,
        course: request.course,
        intent: request.intentTag,
        online: true,
        certified: true,
        unread: 0
      },
      ...current
    ]);
    setConversations((current) => ({
      ...current,
      [menteeId]: [
        {
          id: `request-msg-${Date.now()}`,
          sender: "student",
          text: request.message,
          timestamp: request.receivedAt
        }
      ]
    }));
    setRoadmaps((current) => ({
      ...current,
      [menteeId]: [
        {
          id: `goal-intake-${Date.now()}`,
          title: `Review ${request.intentTag}`,
          completed: false,
          controlledBy: "alumni"
        }
      ]
    }));
    setActiveMenteeId(menteeId);
    setActiveTab("mentees");
  };

  const selectNotification = (item) => {
    setNotifications((current) =>
      current.map((notification) => (notification.id === item.id ? { ...notification, unread: false } : notification))
    );
    setNotificationOpen(false);
    if (item.id === "alumni-note-1") {
      setActiveTab("mentees");
      setActiveMenteeId("mentee-rahul");
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <header className="flex h-16 items-center justify-between bg-navy px-5 text-white shadow">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              window.location.href = backUrl;
            }}
            className="grid h-10 w-10 place-items-center rounded-md border border-white/20 bg-white/10 transition hover:bg-white/15"
            aria-label="Back to alumni dashboard"
            title="Back to alumni dashboard"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="grid h-10 w-10 place-items-center rounded-md bg-white/10">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold">Alumni Guidance</h1>
            <p className="text-sm text-blue-100">
              {mentorshipUsers.alumni.title}, {mentorshipUsers.alumni.company}
            </p>
          </div>
        </div>
        <NotificationMenu
          notifications={notifications}
          open={notificationOpen}
          onToggle={() => setNotificationOpen((open) => !open)}
          onSelect={selectNotification}
        />
      </header>

      <main className="grid h-[calc(100vh-4rem)] grid-cols-1 overflow-hidden lg:grid-cols-[22rem_minmax(0,1fr)_24rem]">
        <PipelineSidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          requests={requests}
          onAccept={acceptRequest}
          activeMentees={activeMentees}
          activeMenteeId={activeMenteeId}
          setActiveMenteeId={setActiveMenteeId}
        />

        <section className="flex min-h-0 flex-col bg-white">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-950">{activeMentee.name}</h2>
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-1 text-xs font-bold text-amber-700">
                  <BadgeCheck className="h-3.5 w-3.5" />
                  Certified
                </span>
              </div>
              <p className="text-sm text-slate-500">{activeMentee.intent}</p>
            </div>
            <MessageCircle className="h-5 w-5 text-navy" />
          </div>

          <MessageStream messages={activeMessages} />

          <div className="border-t border-slate-200 bg-white p-4">
            <div className="mx-auto max-w-4xl space-y-3">
              <div className="flex flex-wrap gap-2">
                {quickActionResponses.map((response) => (
                  <button
                    type="button"
                    key={response}
                    onClick={() => sendMessage(response)}
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-gold hover:bg-amber-50 hover:text-amber-700"
                  >
                    {response}
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
                  placeholder="Type guidance for the student"
                  className="min-w-0 flex-1 rounded-md border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-navy focus:ring-2 focus:ring-blue-100"
                />
                <button
                  type="button"
                  onClick={() => sendMessage()}
                  className="inline-flex items-center gap-2 rounded-md bg-gold px-5 py-3 text-sm font-bold text-white transition hover:bg-amber-600"
                >
                  <Send className="h-4 w-4" />
                  Send
                </button>
              </div>
            </div>
          </div>
        </section>

        <RoadmapControlPanel milestones={activeMilestones} setMilestones={updateActiveMilestones} />
      </main>
    </div>
  );
}
