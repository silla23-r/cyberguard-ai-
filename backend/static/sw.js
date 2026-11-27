self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { raw_context: event.data ? event.data.text() : "Suspicious scam detected." };
  }

  const severity = data.severity || "DANGER";
  const score = data.risk_score ?? 0;
  const label = data.protected_user_label || "Family Member";
  const archetype = String(data.scam_archetype || "SCAM_ALERT").replace(/_/g, " ");
  const title = `[${severity} ${score}/100] ${label} — CyberGuard Alert`;
  const body = `${archetype}: ${data.raw_context || "Potential fraud activity detected."}`;

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: "/static/logo.svg",
      badge: "/static/logo.svg",
      tag: data.alert_id || "cyberguard-guardian",
      requireInteraction: severity === "DANGER",
      data: { url: data.action_url || "/" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});
