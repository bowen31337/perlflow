import React from 'react';
import { clsx } from 'clsx';
import type { IncentiveOfferData } from '../types';

interface IncentiveOfferProps {
  offer: IncentiveOfferData;
  onAccept: () => void;
  onDecline: () => void;
  className?: string;
}

/**
 * Incentive offer card for appointment rescheduling.
 */
export function IncentiveOffer({
  offer,
  onAccept,
  onDecline,
  className,
}: IncentiveOfferProps): JSX.Element {
  const formatDateTime = (date: Date): string => {
    return date.toLocaleString('en-AU', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getIncentiveDisplay = () => {
    switch (offer.incentiveType) {
      case 'discount':
        return { icon: '💰', label: `${offer.incentiveValue} off your visit` };
      case 'priority_slot':
        return { icon: '⭐', label: `Priority ${offer.incentiveValue}` };
      case 'gift':
        return { icon: '🎁', label: offer.incentiveValue };
      default:
        return { icon: '🎉', label: offer.incentiveValue };
    }
  };

  const incentive = getIncentiveDisplay();
  const timeRemaining = Math.max(
    0,
    Math.ceil((offer.expiresAt.getTime() - Date.now()) / (1000 * 60 * 60))
  );

  return (
    <div
      className={clsx(
        'pf-p-4 pf-bg-gradient-to-br pf-from-primary/10 pf-to-primary/5',
        'pf-border pf-border-primary/20 pf-rounded-xl',
        className
      )}
    >
      {/* Header */}
      <div className="pf-flex pf-items-start pf-justify-between pf-mb-3">
        <div>
          <p className="pf-text-sm pf-font-semibold pf-text-gray-900">
            Special Offer for You!
          </p>
          <p className="pf-text-xs pf-text-gray-500 pf-mt-1">
            We have a better time available
          </p>
        </div>
        {timeRemaining > 0 && (
          <span className="pf-text-xs pf-bg-warning/20 pf-text-warning pf-px-2 pf-py-1 pf-rounded-full">
            Expires in {timeRemaining}h
          </span>
        )}
      </div>

      {/* Offer details */}
      <div className="pf-bg-white pf-rounded-lg pf-p-3 pf-mb-4">
        {/* Time change */}
        <div className="pf-flex pf-items-center pf-gap-2 pf-text-sm">
          <span className="pf-text-gray-500 pf-line-through">
            {formatDateTime(offer.originalTime)}
          </span>
          <span className="pf-text-gray-400">→</span>
          <span className="pf-font-medium pf-text-primary">
            {formatDateTime(offer.proposedTime)}
          </span>
        </div>

        {/* Incentive */}
        <div className="pf-flex pf-items-center pf-gap-2 pf-mt-3 pf-pt-3 pf-border-t pf-border-gray-100">
          <span className="pf-text-xl">{incentive.icon}</span>
          <span className="pf-text-sm pf-font-medium pf-text-gray-900">
            {incentive.label}
          </span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="pf-flex pf-gap-2">
        <button
          onClick={onDecline}
          className={clsx(
            'pf-flex-1 pf-py-2 pf-px-4 pf-rounded-full pf-text-sm pf-font-medium',
            'pf-bg-gray-100 pf-text-gray-700',
            'hover:pf-bg-gray-200 pf-transition-colors'
          )}
        >
          Keep Original
        </button>
        <button
          onClick={onAccept}
          className={clsx(
            'pf-flex-1 pf-py-2 pf-px-4 pf-rounded-full pf-text-sm pf-font-medium',
            'pf-bg-primary pf-text-white',
            'hover:pf-bg-primary/90 pf-transition-colors'
          )}
        >
          Accept Offer
        </button>
      </div>

      {/* Note */}
      <p className="pf-text-xs pf-text-gray-500 pf-text-center pf-mt-3">
        This offer is completely voluntary. No pressure!
      </p>
    </div>
  );
}
