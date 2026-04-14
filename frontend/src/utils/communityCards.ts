import type { CommunityTripCard } from '@/types'

const COMMUNITY_CARD_LIST_KEY = 'communityVisibleCards'
const COMMUNITY_SELECTED_CARD_KEY = 'communitySelectedCard'

const parseStoredCards = (raw: string | null): CommunityTripCard[] => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const saveCommunityCards = (cards: CommunityTripCard[]) => {
  sessionStorage.setItem(COMMUNITY_CARD_LIST_KEY, JSON.stringify(cards))
}

export const readCommunityCards = () => parseStoredCards(sessionStorage.getItem(COMMUNITY_CARD_LIST_KEY))

export const saveSelectedCommunityCard = (card: CommunityTripCard) => {
  sessionStorage.setItem(COMMUNITY_SELECTED_CARD_KEY, JSON.stringify(card))
}

export const readSelectedCommunityCard = (cardId?: string) => {
  const raw = sessionStorage.getItem(COMMUNITY_SELECTED_CARD_KEY)
  if (!raw) return null
  try {
    const card = JSON.parse(raw) as CommunityTripCard
    if (!card?.id) return null
    if (cardId && card.id !== cardId) return null
    return card
  } catch {
    return null
  }
}

export const upsertStoredCommunityCard = (card: CommunityTripCard) => {
  const cards = readCommunityCards()
  const index = cards.findIndex((item) => item.id === card.id)
  if (index >= 0) {
    cards.splice(index, 1, card)
  } else {
    cards.unshift(card)
  }
  saveCommunityCards(cards)
  saveSelectedCommunityCard(card)
}
