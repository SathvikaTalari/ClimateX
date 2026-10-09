import type { Metadata } from 'next';
import './globals.css';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'ClimateX — AI Earth Intelligence & Climate Action Platform',
  description: 'Next-generation Earth observation, climate risk intelligence, and collaborative action platform powered by satellite telemetry and spatial intelligence.',
  keywords: ['ClimateX', 'Earth Intelligence', 'Satellite Telemetry', 'Climate Action', 'MapLibre', 'Environmental Dashboard', 'Remote Sensing'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const storedTheme = localStorage.getItem('climatex-theme');
                if (storedTheme === 'light') {
                  document.documentElement.classList.remove('dark');
                  document.documentElement.classList.add('light');
                } else {
                  document.documentElement.classList.add('dark');
                  document.documentElement.classList.remove('light');
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className="bg-slate-100 text-slate-900 dark:bg-earth-950 dark:text-slate-100 min-h-screen flex flex-col font-sans transition-colors duration-300">
        <Providers>
          <Header />
          <div className="flex-1 flex overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
