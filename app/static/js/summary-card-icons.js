const summaryIconRules = [
  [/signed|profile|student|teacher|admin|alumni|user/i, "ID", "primary"],
  [/role|portal/i, "R", "slate"],
  [/module|ai/i, "AI", "primary"],
  [/attendance|present/i, "%", "success"],
  [/biometric|face|verified/i, "OK", "success"],
  [/section|class/i, "C", "info"],
  [/roll|enrollment/i, "#", "slate"],
  [/department/i, "D", "primary"],
  [/branch/i, "B", "info"],
  [/semester/i, "S", "warning"],
  [/academic|year/i, "Y", "slate"],
  [/subject|course/i, "SB", "primary"],
  [/session|recent/i, "SE", "info"],
  [/record|analysis|analytics/i, "AN", "warning"],
  [/event/i, "EV", "warning"],
  [/room|location/i, "RM", "info"],
  [/next|today|time|schedule/i, "T", "info"],
  [/job|internship|opportunit/i, "OP", "success"],
  [/document|quiz|test|notes/i, "QT", "primary"],
  [/status|health/i, "ST", "danger"],
  [/count|total|available/i, "#", "slate"],
];

document.querySelectorAll(".summary-card").forEach((card) => {
  const label = (card.querySelector("span")?.textContent || "").trim();
  const match = summaryIconRules.find(([pattern]) => pattern.test(label));
  if (!card.dataset.cardIcon) {
    card.dataset.cardIcon = match ? match[1] : "SC";
  }
  if (!card.dataset.cardTone) {
    card.dataset.cardTone = match ? match[2] : "primary";
  }
});
