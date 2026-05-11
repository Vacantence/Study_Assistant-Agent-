import { useEffect } from 'react';
import { useReviewStore } from '../stores/reviewStore';

const RATINGS = [
  { value: 1, label: '完全忘了' },
  { value: 2, label: '很模糊' },
  { value: 3, label: '有点印象' },
  { value: 4, label: '基本记住' },
  { value: 5, label: '非常熟练' },
];

export default function ReviewPage() {
  const { cards, currentIndex, showAnswer, loading, fetchCards, revealAnswer, rateCard, deleteCard } = useReviewStore();

  useEffect(() => { fetchCards(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p style={{ color: 'var(--color-text-muted)' }}>加载中...</p>
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h2 className="text-lg font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>暂无待复习卡片</h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>继续学习来生成新卡片</p>
        </div>
      </div>
    );
  }

  const card = cards[currentIndex];

  return (
    <div className="flex flex-col items-center justify-center h-full p-4">
      <div className="w-full max-w-2xl">
        <div className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
          第 {currentIndex + 1} / {cards.length} 张 | 主题: {card.topic}
        </div>

        <div
          className="border rounded-xl p-6 mb-4"
          style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
        >
          <div className="text-base leading-relaxed">{card.question}</div>
        </div>

        {!showAnswer ? (
          <button
            onClick={revealAnswer}
            className="w-full py-2.5 rounded-xl text-white text-sm font-medium transition-colors cursor-pointer"
            style={{ backgroundColor: 'var(--color-accent)' }}
          >
            显示答案
          </button>
        ) : (
          <>
            <div
              className="border rounded-xl p-6 mb-4"
              style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-accent)' }}
            >
              <div className="text-base leading-relaxed">{card.answer}</div>
            </div>

            <p className="text-xs mb-2" style={{ color: 'var(--color-text-muted)' }}>自我评分：</p>
            <div className="flex gap-2 mb-3">
              {RATINGS.map((r) => (
                <button
                  key={r.value}
                  onClick={() => rateCard(r.value)}
                  className="flex-1 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer"
                  style={{
                    backgroundColor: 'var(--color-surface-hover)',
                    color: 'var(--color-text-primary)',
                  }}
                >
                  {r.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => deleteCard(card.id)}
              className="text-xs cursor-pointer"
              style={{ color: 'var(--color-danger)' }}
            >
              删除此卡片
            </button>
          </>
        )}
      </div>
    </div>
  );
}
