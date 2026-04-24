export function formatAvatarBase64(base64Str) {
  if (!base64Str) return null
  if (base64Str.startsWith('data:')) return base64Str
  return `data:image/jpeg;base64,${base64Str}`
}
