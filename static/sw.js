/* Plant Hydration Hub — Web Push service worker */

self.addEventListener("push", (event) => {
  let payload = {
    title: "Plant Hydration Hub",
    body: "A plant needs attention.",
    url: "/",
  };
  try {
    if (event.data) {
      payload = { ...payload, ...event.data.json() };
    }
  } catch (_) {
    try {
      payload.body = event.data ? event.data.text() : payload.body;
    } catch (_) {
      /* keep defaults */
    }
  }

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: "/static/icon.svg",
      badge: "/static/icon.svg",
      data: { url: payload.url || "/" },
      tag: "plant-dry-alert",
      renotify: true,
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ("focus" in client) {
          client.navigate(target);
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(target);
      }
      return undefined;
    })
  );
});
