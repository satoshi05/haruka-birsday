'use client';

import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import memories from '@/data/memories.json';

type Photo = (typeof memories.chapters)[number]['photos'][number];

function MemoryPhoto({ photo, className = '', eager = false }: { photo: Photo; className?: string; eager?: boolean }) {
  return (
    <picture className={className}>
      <source media="(max-width: 768px)" srcSet={photo.srcSmall} />
      <img loading={eager ? 'eager' : 'lazy'} src={photo.src} alt={photo.alt} />
    </picture>
  );
}

export default function Home() {
  const randomPool = useMemo(() => memories.chapters.flatMap((chapter) => chapter.photos), []);
  const [randomIndex, setRandomIndex] = useState(0);

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
      <section className="opening" aria-labelledby="site-title">
        <div className="opening__grain" />
        <div className="opening__content">
          <p className="eyebrow">Happy Birthday</p>
          <h1 id="site-title">OUR DAYS</h1>
          <a className="start-button" href="#introduction">START</a>
        </div>
        <p className="scroll-note">SCROLL</p>
      </section>

      <section className="introduction" id="introduction">
        <MemoryPhoto photo={memories.chapters[0].photos[0]} className="introduction__photo" eager />
        <div className="introduction__copy reveal">
          <p className="section-label">MEMORY BOOK</p>
          <h2>二人で過ごした日々。</h2>
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

      <section className="video-memories">
        <header className="section-heading reveal">
          <p className="section-label section-label--light">VIDEO MEMORIES</p>
          <h2>動いている思い出。</h2>
        </header>
        <div className="video-grid">
          {memories.chapters.filter((chapter) => chapter.videos[0]).map((chapter) => (
            <figure className="video-card reveal" key={chapter.number}>
              <video controls playsInline preload="none" aria-label={chapter.videos[0].label}>
                <source src={chapter.videos[0].src} type="video/mp4" />
              </video>
              <figcaption>{chapter.title}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section className="our-next">
        <p className="section-label reveal">OUR NEXT</p>
        <h2 className="reveal">これから。</h2>
        <ul className="next-list">
          <li className="reveal"><span>01</span>次に行きたい場所</li>
          <li className="reveal"><span>02</span>一緒にやりたいこと</li>
          <li className="reveal"><span>03</span>また見たい景色</li>
        </ul>
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
