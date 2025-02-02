import { Outfit } from "next/font/google";

import "./globals.css";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

const outfit = Outfit({ subsets: ["latin"] });

export const metadata = {
  title: "POI DEMO",
  description: "POI DEMO FROM WEB",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet" />
      </head>

      <body
        className={outfit.className}
      >
        <Navbar />
        <div className="h-[94vh] pt-28 overflow-y-auto " >
          {children}
        </div>
        <Footer />
      </body>
    </html>
  );
}
