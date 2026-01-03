'use client';

import { PearlFlowProvider, ChatWidget } from '@pearlflow/chat-ui';
import '@pearlflow/chat-ui/style.css';

/**
 * Demo Homepage
 *
 * This page demonstrates the PearlFlow chat widget integration.
 * The widget can be embedded in any React application with minimal setup.
 */
export default function HomePage() {
  return (
    <PearlFlowProvider
      apiKey="pf_test_demo_key_12345"
      apiUrl={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}
      theme={{
        primary: '#00D4FF',
        secondary: '#10B981',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
        <div className="container mx-auto px-4 py-16">
          <header className="text-center mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              PearlFlow Demo
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Experience the future of dental practice management with our AI-powered assistant.
              Click the chat button in the bottom-right corner to get started.
            </p>
          </header>

          <main className="max-w-4xl mx-auto space-y-12">
            <section className="bg-white rounded-2xl shadow-lg p-8">
              <h2 className="text-3xl font-semibold text-gray-800 mb-4">
                Intelligent Triage
              </h2>
              <p className="text-gray-600 leading-relaxed">
                Our AI-powered triage system assesses patient symptoms with empathy and precision.
                Try telling the assistant about a toothache or dental emergency.
              </p>
            </section>

            <section className="bg-white rounded-2xl shadow-lg p-8">
              <h2 className="text-3xl font-semibold text-gray-800 mb-4">
                Smart Scheduling
              </h2>
              <p className="text-gray-600 leading-relaxed">
                Book appointments instantly with our intelligent scheduling system.
                The assistant finds the perfect time slot based on your preferences and clinic availability.
              </p>
            </section>

            <section className="bg-white rounded-2xl shadow-lg p-8">
              <h2 className="text-3xl font-semibold text-gray-800 mb-4">
                24/7 Availability
              </h2>
              <p className="text-gray-600 leading-relaxed">
                Never miss a patient inquiry. Our AI assistant is always ready to help,
                whether it's for emergency triage or routine appointment booking.
              </p>
            </section>

            <section className="bg-gradient-to-r from-blue-500 to-green-500 rounded-2xl shadow-lg p-8 text-white">
              <h2 className="text-3xl font-semibold mb-4">
                Ready to Try It?
              </h2>
              <p className="text-lg leading-relaxed mb-6">
                Click the floating chat button in the bottom-right corner of this page
                to start a conversation with the PearlFlow Assistant.
              </p>
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                  ✅ "I have a toothache"
                </div>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                  ✅ "I need to book a cleaning"
                </div>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                  ✅ "It's an emergency"
                </div>
              </div>
            </section>
          </main>

          <footer className="mt-16 text-center text-gray-600">
            <p className="text-sm">
              Powered by PearlFlow AI • Built for Modern Dental Practices
            </p>
          </footer>
        </div>

        {/* Chat Widget */}
        <ChatWidget position="bottom-right" defaultOpen={false} />
      </div>
    </PearlFlowProvider>
  );
}
