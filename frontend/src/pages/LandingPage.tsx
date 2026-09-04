import React from 'react';

import { FinalCTASection } from '../components/landing/FinalCTASection';
import { Footer } from '../components/layout/Footer';
import { Header } from '../components/layout/Header';
import { HeroSection } from '../components/landing/HeroSection';
import { HowItWorksSection } from '../components/landing/HowItWorksSection';
import { MasterDocumentStage } from '../components/visuals/MasterDocumentStage';
import { ProblemSection } from '../components/landing/ProblemSection';
import { ProductRevealSection } from '../components/landing/ProductRevealSection';
import { UseCasesSection } from '../components/landing/UseCasesSection';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#F8F7FC] text-[#1E1B24] font-sans antialiased selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
      {/* Global Header */}
      <Header />

      {/* Main Landing Story Narrative */}
      <main className="flex-1">
        <HeroSection />
        
        {/* Flagship Sticky Document Story Stage (#document-stage) */}
        <section id="document-stage" className="py-12 bg-[#F8F7FC] border-t border-[#1E1B24]/08">
          <MasterDocumentStage />
        </section>

        <ProblemSection />
        <HowItWorksSection />
        <UseCasesSection />
        <ProductRevealSection />
        <FinalCTASection />
      </main>

      {/* Global Footer */}
      <Footer />
    </div>
  );
};
