export const avatarText = (name?: string) => (name || '旅').slice(0, 1).toUpperCase()

export const avatarStyle = (name?: string) => {
  const palettes = [
    ['#ff8a65', '#ffd180'],
    ['#4db6ac', '#80cbc4'],
    ['#64b5f6', '#90caf9'],
    ['#9575cd', '#b39ddb'],
    ['#f06292', '#f8bbd0'],
    ['#81c784', '#c5e1a5'],
  ]
  const seed = Array.from(name || 'travel').reduce((total, char) => total + char.charCodeAt(0), 0)
  const [start, end] = palettes[seed % palettes.length]
  return {
    background: `linear-gradient(135deg, ${start}, ${end})`,
  }
}
