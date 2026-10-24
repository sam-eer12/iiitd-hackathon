const base = process.env.SMOKE_BASE_URL ?? "http://127.0.0.1:3000";
for (let attempt = 0; attempt < 60; attempt++) {
  try {
    const response = await fetch(`${base}/api/health`);
    if (response.ok) process.exit(0);
  } catch {}
  await new Promise((resolve) => setTimeout(resolve, 1000));
}
throw new Error("Web/API/database did not become ready within 60 seconds.");
