export function buildUrl(path: string) {
  const base = import.meta.env.BASE_URL;
  const baseNormalized = base.replace(/\/+$/, '');
  const pathNormalized = path.replace(/^\/+/, '');
  return new URL(`${baseNormalized}/${pathNormalized}`, window.location.origin).toString();
}
