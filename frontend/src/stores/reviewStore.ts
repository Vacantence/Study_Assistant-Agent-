import { create } from 'zustand';
import type { ReviewCard } from '../types';
import { reviewApi } from '../api/review';

interface ReviewState {
  cards: ReviewCard[];
  currentIndex: number;
  showAnswer: boolean;
  loading: boolean;

  fetchCards: () => Promise<void>;
  revealAnswer: () => void;
  rateCard: (quality: number) => Promise<void>;
  deleteCard: (id: number) => Promise<void>;
}

export const useReviewStore = create<ReviewState>((set, get) => ({
  cards: [],
  currentIndex: 0,
  showAnswer: false,
  loading: false,

  fetchCards: async () => {
    set({ loading: true });
    const cards = await reviewApi.getDueCards();
    set({ cards, currentIndex: 0, showAnswer: false, loading: false });
  },

  revealAnswer: () => set({ showAnswer: true }),

  rateCard: async (quality) => {
    const { cards, currentIndex } = get();
    const card = cards[currentIndex];
    if (!card) return;
    await reviewApi.reviewCard(card.id, quality);
    if (currentIndex < cards.length - 1) {
      set({ currentIndex: currentIndex + 1, showAnswer: false });
    } else {
      set({ cards: [], currentIndex: 0, showAnswer: false });
    }
  },

  deleteCard: async (id) => {
    await reviewApi.deleteCard(id);
    const { cards, currentIndex } = get();
    const newCards = cards.filter(c => c.id !== id);
    if (newCards.length === 0) {
      set({ cards: [], currentIndex: 0, showAnswer: false });
    } else if (currentIndex >= newCards.length) {
      set({ cards: newCards, currentIndex: newCards.length - 1, showAnswer: false });
    } else {
      set({ cards: newCards, showAnswer: false });
    }
  },
}));
