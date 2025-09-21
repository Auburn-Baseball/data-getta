export function buildBaseUrl() {
  const base = import.meta.env.BASE_URL;
  const url = new URL(base, window.location.origin).toString();
  console.log(url);
  return url;
}
