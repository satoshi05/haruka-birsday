'use client';

import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import memories from '@/data/memories.json';

type Photo = (typeof memories.chapters)[number]['photos'][number];

function MemoryPhoto({ photo, className = '', eager = false, onLoad }: { photo: Photo; className?: string; eager?: boolean; onLoad?: () => void }) {
  return (
    <picture className={className}>
      <source media="(max-width: 768px)" srcSet={photo.srcSmall} />
      <img loading={eager ? 'eager' : 'lazy'} src={photo.src} alt={photo.alt} onLoad={onLoad} />
    </picture>
  );
}

export default function Home() {
  const randomPool = useMemo(() => memories.chapters.flatMap((chapter) => chapter.photos), []);
  const introPool = useMemo(() => [
    memories.chapters[2].photos[8],
    memories.chapters[3].photos[3],
    memories.chapters[4].photos[0],
  ], []);
  const [randomIndex, setRandomIndex] = useState(0);
  const [introViews, setIntroViews] = useState(0);
  const [introLoading, setIntroLoading] = useState(false);

  useEffect(() => {
    document.body.style.overflow = introViews < 3 ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [introViews]);

  useEffect(() => {
    introPool.forEach((photo) => {
      const preload = new Image();
      preload.src = photo.srcSmall;
    });
  }, [introPool]);

  const openMemory = () => {
    if (introViews >= 3) return;
    const nextView = introViews + 1;
    setIntroLoading(true);
    setIntroViews(nextView);
    if (nextView === 3) {
      window.setTimeout(() => document.querySelector('.timeline')?.scrollIntoView({ behavior: 'smooth' }), 250);
    }
  };

  const showAnotherMemory = () => {
    if (randomPool.length < 2) return;
    setRandomIndex((current) => {
      let next = current;
      while (next === current) next = Math.floor(Math.random() * randomPool.length);
      return next;
    });
  };

  return (
    <main>
      <section className={`opening ${introViews ? 'opening--memory' : ''}`} aria-labelledby="site-title">
        <div className="opening__grain" />
        {introViews > 0 && (
          <MemoryPhoto
            key={introPool[introViews - 1].src}
            photo={introPool[introViews - 1]}
            className="opening-memory"
            eager
            onLoad={() => setIntroLoading(false)}
          />
        )}
        {introLoading && <div className="opening-loader" role="status" aria-label="写真を読み込み中"><span /></div>}
        <div className="opening__content">
          {introViews === 0 && <h1 id="site-title">Happy Birthday<br />Haruka.</h1>}
          {introViews < 3 && (
            <button className="opening-trigger" onClick={openMemory} type="button" disabled={introLoading}>
              <span>{introLoading ? '読み込み中' : introViews === 0 ? '思い出を見る' : 'もう一枚'}</span>
              <small>{introViews} / 3</small>
            </button>
          )}
        </div>
      </section>

      <section className="timeline" aria-label="思い出のタイムライン">
        {memories.chapters.map((chapter, chapterIndex) => (
          <article className="chapter" key={chapter.number}>
            <header className="chapter__header reveal">
              <p className="chapter-number">CHAPTER {String(chapterIndex + 1).padStart(2, '0')}</p>
              <h2>{chapter.title}</h2>
            </header>

            <MemoryPhoto photo={chapter.photos[0]} className="chapter__hero reveal" />

            <div className="chapter__gallery">
              {chapter.photos.slice(1, 5).map((photo, photoIndex) => (
                <MemoryPhoto
                  key={photo.src}
                  photo={photo}
                  className={`chapter__tile chapter__tile--${photoIndex + 1} reveal`}
                />
              ))}
              {chapter.videos[0] && (
                <figure className="chapter__tile chapter__tile--video reveal">
                  <video autoPlay muted loop playsInline preload="metadata" aria-label={chapter.videos[0].label}>
                    <source src={chapter.videos[0].src} type="video/mp4" />
                  </video>
                </figure>
              )}
            </div>

          </article>
        ))}
      </section>

      <section className="random-memory">
        <div className="random-memory__heading reveal">
          <p className="section-label">RANDOM MEMORIES</p>
          <h2>思い出を見る</h2>
        </div>
        <MemoryPhoto key={randomPool[randomIndex].src} photo={randomPool[randomIndex]} className="random-memory__photo" />
        <Button className="random-button" onClick={showAnotherMemory}>もう一枚</Button>
      </section>

      <section className="birthday-message">
        <p className="section-label section-label--light reveal">FOR HARUKA</p>
        <div className="message-lines">
          <p className="reveal">一緒にいれて幸せです。</p>
          <p className="reveal">29歳の1年間も</p>
          <p className="reveal">一緒に楽しもう！</p>
          <p className="reveal">いつもありがとう！</p>
        </div>
      </section>

      <footer className="ending">
        <p>Happy Birthday.</p>
        <p>To be continued...</p>
      </footer>
    </main>
  );
}
