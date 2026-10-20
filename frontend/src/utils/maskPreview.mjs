export function storagePreviewUrl(value, origin) {
  if (!value) return ''
  try {
    const url = new URL(value, origin)
    const expected = new URL(origin)
    return url.origin === expected.origin && url.pathname.startsWith('/storage/') ? url.href : ''
  } catch { return '' }
}

// Only the display buffer changes; uploaded and generated files are untouched.
export function maskDrawingPixels(source, width, height) {
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1 || source.length !== width * height * 4) {
    throw new RangeError('Invalid mask preview dimensions')
  }
  const coverage = new Uint8ClampedArray(width * height)
  let hasAlpha = false
  for (let i = 3; i < source.length; i += 4) if (source[i] !== 255) { hasAlpha = true; break }
  for (let i = 0; i < coverage.length; i++) {
    const offset = i * 4
    coverage[i] = hasAlpha ? source[offset + 3] : Math.round(source[offset] * 0.2126 + source[offset + 1] * 0.7152 + source[offset + 2] * 0.0722)
  }
  const result = new Uint8ClampedArray(source.length)
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const index = y * width + x
      const alpha = coverage[index]
      if (!alpha) continue
      const edge = x === 0 || y === 0 || x === width - 1 || y === height - 1 ||
        coverage[index - 1] < alpha || coverage[index + 1] < alpha ||
        coverage[index - width] < alpha || coverage[index + width] < alpha
      const offset = index * 4
      result[offset] = edge ? 52 : 233
      result[offset + 1] = edge ? 59 : 228
      result[offset + 2] = edge ? 56 : 216
      result[offset + 3] = alpha
    }
  }
  return result
}

export function drawingFrame(width, height) {
  const ratio = Number(width) / Number(height)
  if (!Number.isFinite(ratio) || ratio <= 0) return null
  const scale = Math.min(660 / width, 202 / height)
  const w = width * scale
  const h = height * scale
  return { x: 60 + (660 - w) / 2, y: 68 + (202 - h) / 2, width: w, height: h }
}
