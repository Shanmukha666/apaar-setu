export const maskApaar = (id: string) => `••••••••${id.slice(-4)}`;
export const formatTime = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
};
export const label = (code: string) => code.replaceAll("_", " ").toLowerCase();
