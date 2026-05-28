export const messageSchemaExample = {
  id: "msg-schema-example",
  sender: "student",
  text: "Shared backend-ready mentorship message.",
  timestamp: "10:30 AM"
};

export const mentorshipUsers = {
  student: {
    id: "student-sagar",
    name: "Sagar Senapati",
    role: "student",
    title: "Final Year CSE Student",
    department: "Computer Science",
    graduationYear: "2026"
  },
  alumni: {
    id: "alumni-rohit",
    name: "Rohit Mehra",
    role: "alumni",
    title: "Senior Software Engineer",
    company: "Microsoft",
    verified: true
  }
};

export const mentors = [
  {
    id: "mentor-rohit",
    name: "Rohit Mehra",
    company: "SDE at Microsoft",
    expertise: "Backend Systems",
    active: true,
    unread: 2,
    certified: true
  },
  {
    id: "mentor-sagarika",
    name: "Sagarika Nair",
    company: "Product Manager at Google",
    expertise: "Product Interviews",
    active: false,
    unread: 0,
    certified: true
  },
  {
    id: "mentor-ananya",
    name: "Ananya Rao",
    company: "Data Engineer at Atlassian",
    expertise: "Data Platforms",
    active: true,
    unread: 1,
    certified: false
  }
];

export const mentees = [
  {
    id: "mentee-sagar",
    name: "Sagar Senapati",
    course: "B.Tech CSE",
    intent: "Backend placement preparation",
    online: true,
    certified: true,
    unread: 1
  },
  {
    id: "mentee-neha",
    name: "Neha Sharma",
    course: "B.Tech IT",
    intent: "Resume and internship search",
    online: false,
    certified: true,
    unread: 0
  },
  {
    id: "mentee-rahul",
    name: "Rahul Verma",
    course: "B.Tech CSE",
    intent: "Mock interview practice",
    online: true,
    certified: true,
    unread: 3
  }
];

export const mentorConversations = {
  "mentor-rohit": [
    {
      id: "msg-rohit-1",
      sender: "student",
      text: "Hello sir, I am preparing for backend developer roles and need help structuring my plan.",
      timestamp: "10:12 AM"
    },
    {
      id: "msg-rohit-2",
      sender: "alumni",
      text: "Start with your resume and GitHub profile. I will review both and then plan a mock session.",
      timestamp: "10:14 AM"
    },
    {
      id: "msg-rohit-3",
      sender: "student",
      text: "I have uploaded the resume draft. My main concern is project impact and ATS readability.",
      timestamp: "10:17 AM"
    },
    {
      id: "msg-rohit-4",
      sender: "alumni",
      text: "Good. I added a roadmap: profile review first, then GitHub cleanup, then mock interview day one.",
      timestamp: "10:21 AM"
    }
  ],
  "mentor-sagarika": [
    {
      id: "msg-sagarika-1",
      sender: "alumni",
      text: "Send me two product ideas you want to discuss. We will convert them into interview stories.",
      timestamp: "Yesterday"
    },
    {
      id: "msg-sagarika-2",
      sender: "student",
      text: "I will share the campus event app and attendance automation case studies.",
      timestamp: "09:08 AM"
    }
  ],
  "mentor-ananya": [
    {
      id: "msg-ananya-1",
      sender: "alumni",
      text: "Your data project needs a clearer problem statement and result metric.",
      timestamp: "08:40 AM"
    },
    {
      id: "msg-ananya-2",
      sender: "student",
      text: "I can add ingestion latency and dashboard adoption numbers.",
      timestamp: "08:46 AM"
    }
  ]
};

export const menteeConversations = {
  "mentee-sagar": mentorConversations["mentor-rohit"],
  "mentee-neha": [
    {
      id: "msg-neha-1",
      sender: "student",
      text: "Ma'am, can you review whether my internship resume is too project-heavy?",
      timestamp: "09:55 AM"
    },
    {
      id: "msg-neha-2",
      sender: "alumni",
      text: "Keep the top two projects and add one strong internship objective line.",
      timestamp: "10:02 AM"
    }
  ],
  "mentee-rahul": [
    {
      id: "msg-rahul-1",
      sender: "student",
      text: "I uploaded the new resume PDF and want a mock interview this week.",
      timestamp: "10:05 AM"
    },
    {
      id: "msg-rahul-2",
      sender: "alumni",
      text: "I will review the PDF first, then we can schedule a 45-minute backend mock.",
      timestamp: "10:09 AM"
    }
  ]
};

export const mentorshipRequests = [
  {
    id: "request-amit",
    studentId: "student-amit",
    studentName: "Amit Kumar",
    course: "CSE, 3rd Year",
    intentTag: "Mock Interview Request",
    message: "I want to practice DSA and system design before internship interviews.",
    receivedAt: "09:45 AM"
  },
  {
    id: "request-priya",
    studentId: "student-priya",
    studentName: "Priya Singh",
    course: "ECE, Final Year",
    intentTag: "Resume Review",
    message: "Please review my resume for software developer roles.",
    receivedAt: "10:05 AM"
  },
  {
    id: "request-kabir",
    studentId: "student-kabir",
    studentName: "Kabir Das",
    course: "IT, 2nd Year",
    intentTag: "Career Guidance",
    message: "I need help choosing between data engineering and backend development.",
    receivedAt: "10:22 AM"
  }
];

export const mentorshipMessages = [
  {
    id: "msg-1",
    sender: "student",
    text: "Hello sir, I am preparing for backend developer roles and need help structuring my plan.",
    timestamp: "10:12 AM"
  },
  {
    id: "msg-2",
    sender: "alumni",
    text: "Start with your resume and GitHub profile. I will review both and then plan a mock session.",
    timestamp: "10:14 AM"
  },
  {
    id: "msg-3",
    sender: "student",
    text: "I have uploaded the resume draft. My main concern is project impact and ATS readability.",
    timestamp: "10:17 AM"
  },
  {
    id: "msg-4",
    sender: "alumni",
    text: "Good. I added a roadmap: profile review first, then GitHub cleanup, then mock interview day one.",
    timestamp: "10:21 AM"
  }
];

export const initialMilestones = [
  {
    id: "goal-profile",
    title: "Complete Profile Review",
    completed: true,
    controlledBy: "alumni"
  },
  {
    id: "goal-resume",
    title: "Resume ATS Cleanup",
    completed: true,
    controlledBy: "alumni"
  },
  {
    id: "goal-github",
    title: "Share GitHub Link",
    completed: false,
    controlledBy: "alumni"
  },
  {
    id: "goal-mock-1",
    title: "Mock Interview Day 1",
    completed: false,
    controlledBy: "alumni"
  }
];

export const mentorMilestones = {
  "mentor-rohit": initialMilestones,
  "mentor-sagarika": [
    {
      id: "goal-product-story",
      title: "Prepare Two Product Stories",
      completed: true,
      controlledBy: "alumni"
    },
    {
      id: "goal-case-study",
      title: "Rewrite Case Study Metrics",
      completed: false,
      controlledBy: "alumni"
    },
    {
      id: "goal-pm-mock",
      title: "Product Sense Mock Session",
      completed: false,
      controlledBy: "alumni"
    }
  ],
  "mentor-ananya": [
    {
      id: "goal-data-profile",
      title: "Data Portfolio Review",
      completed: true,
      controlledBy: "alumni"
    },
    {
      id: "goal-pipeline-diagram",
      title: "Add Pipeline Architecture Diagram",
      completed: false,
      controlledBy: "alumni"
    },
    {
      id: "goal-sql-round",
      title: "SQL Interview Drill",
      completed: false,
      controlledBy: "alumni"
    }
  ]
};

export const menteeMilestones = {
  "mentee-sagar": initialMilestones,
  "mentee-neha": [
    {
      id: "goal-neha-resume",
      title: "Shortlist Resume Projects",
      completed: true,
      controlledBy: "alumni"
    },
    {
      id: "goal-neha-cover",
      title: "Draft Internship Outreach Message",
      completed: false,
      controlledBy: "alumni"
    }
  ],
  "mentee-rahul": [
    {
      id: "goal-rahul-resume",
      title: "Review Uploaded Resume PDF",
      completed: false,
      controlledBy: "alumni"
    },
    {
      id: "goal-rahul-mock",
      title: "Schedule Backend Mock Interview",
      completed: false,
      controlledBy: "alumni"
    }
  ]
};

export const studentNotifications = [
  {
    id: "student-note-1",
    title: "Resume checklist approved",
    body: "Alumnus Sagar approved your resume checklist.",
    unread: true,
    timestamp: "2 min ago"
  },
  {
    id: "student-note-2",
    title: "New message from Mentor Rohit",
    body: "Rohit sent a roadmap update for your mock interview.",
    unread: true,
    timestamp: "9 min ago"
  },
  {
    id: "student-note-3",
    title: "Milestone unlocked",
    body: "Complete GitHub profile review to move forward.",
    unread: true,
    timestamp: "18 min ago"
  }
];

export const alumniNotifications = [
  {
    id: "alumni-note-1",
    title: "Resume PDF uploaded",
    body: "Student Rahul uploaded a new Resume PDF.",
    unread: true,
    timestamp: "4 min ago"
  },
  {
    id: "alumni-note-2",
    title: "New connection request",
    body: "Amit from CSE requested a mock interview.",
    unread: true,
    timestamp: "12 min ago"
  },
  {
    id: "alumni-note-3",
    title: "Roadmap update pending",
    body: "Sagar is waiting for the next milestone.",
    unread: false,
    timestamp: "28 min ago"
  }
];

export const quickActionResponses = [
  "Please share your GitHub link.",
  "Let's schedule a mock session.",
  "Upload your latest resume PDF.",
  "Add measurable impact to your project bullets."
];

export const sharedMentorshipThreadKey = "mentorship-thread-sagar-rohit";
export const sharedMentorshipChannelName = "mentorship-thread-updates";

export function readSharedMentorshipThread(fallbackMessages) {
  try {
    const saved = window.localStorage.getItem(sharedMentorshipThreadKey);
    if (!saved) return fallbackMessages;
    const parsed = JSON.parse(saved);
    return Array.isArray(parsed) ? parsed : fallbackMessages;
  } catch {
    return fallbackMessages;
  }
}

export function writeSharedMentorshipThread(messages) {
  window.localStorage.setItem(sharedMentorshipThreadKey, JSON.stringify(messages));
  if ("BroadcastChannel" in window) {
    const channel = new BroadcastChannel(sharedMentorshipChannelName);
    channel.postMessage(messages);
    channel.close();
  }
}

export function currentTimestamp() {
  return new Intl.DateTimeFormat("en-IN", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true
  }).format(new Date());
}
