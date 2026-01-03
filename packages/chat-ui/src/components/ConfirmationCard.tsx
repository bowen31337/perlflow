import React from 'react';
import { clsx } from 'clsx';
import type { AppointmentConfirmation } from '../types';

interface ConfirmationCardProps {
  confirmation: AppointmentConfirmation;
  className?: string;
}

/**
 * Appointment confirmation card showing booking details.
 */
export function ConfirmationCard({ confirmation, className }: ConfirmationCardProps): JSX.Element {
  const formatDateTime = (date: Date): string => {
    return date.toLocaleString('en-AU', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div
      className={clsx(
        'pf-p-4 pf-bg-secondary/10 pf-border pf-border-secondary/30 pf-rounded-xl',
        className
      )}
    >
      {/* Success header */}
      <div className="pf-flex pf-items-center pf-gap-2 pf-mb-4">
        <div className="pf-w-8 pf-h-8 pf-rounded-full pf-bg-secondary pf-flex pf-items-center pf-justify-center">
          <svg
            className="pf-w-5 pf-h-5 pf-text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <div>
          <p className="pf-text-sm pf-font-semibold pf-text-secondary">Appointment Confirmed!</p>
        </div>
      </div>

      {/* Appointment details */}
      <div className="pf-space-y-3">
        <div>
          <p className="pf-text-xs pf-text-gray-500 pf-uppercase pf-tracking-wide">Patient</p>
          <p className="pf-text-sm pf-font-medium pf-text-gray-900">{confirmation.patientName}</p>
        </div>

        <div>
          <p className="pf-text-xs pf-text-gray-500 pf-uppercase pf-tracking-wide">Procedure</p>
          <p className="pf-text-sm pf-font-medium pf-text-gray-900">{confirmation.procedureName}</p>
        </div>

        <div>
          <p className="pf-text-xs pf-text-gray-500 pf-uppercase pf-tracking-wide">Date & Time</p>
          <p className="pf-text-sm pf-font-medium pf-text-gray-900">
            {formatDateTime(confirmation.startTime)}
          </p>
        </div>

        <div>
          <p className="pf-text-xs pf-text-gray-500 pf-uppercase pf-tracking-wide">Dentist</p>
          <p className="pf-text-sm pf-font-medium pf-text-gray-900">{confirmation.dentistName}</p>
        </div>

        <div className="pf-pt-2 pf-border-t pf-border-secondary/20">
          <p className="pf-text-xs pf-text-gray-600">
            A confirmation email has been sent. Please arrive 10 minutes early.
          </p>
        </div>
      </div>
    </div>
  );
}
