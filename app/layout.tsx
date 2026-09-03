import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OUR DAYS',
  description: '二人で過ごしてきた時間を振り返るMEMORY BOOK',
  openGraph: {
    title: 'OUR DAYS',
    description: 'Happy Birthday',
    images: [{ url: '/og.png', width: 1200, height: 630, alt: 'OUR DAYS — Happy Birthday' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'OUR DAYS',
    description: 'Happy Birthday',
    images: ['/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
