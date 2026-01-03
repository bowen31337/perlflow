import { clsx } from 'clsx';
import type { Slot } from '../types';

interface SlotListProps {
  slots: Slot[];
  onSelect: (slot: Slot) => void;
  className?: string;
}

/**
 * List of available appointment slots for selection.
 */
export function SlotList({ slots, onSelect, className }: SlotListProps): JSX.Element {
  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-AU', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-AU', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });
  };

  // Group slots by date
  const groupedSlots = slots.reduce<Record<string, Slot[]>>((acc, slot) => {
    const dateKey = slot.startTime.toDateString();
    if (!acc[dateKey]) {
      acc[dateKey] = [];
    }
    acc[dateKey].push(slot);
    return acc;
  }, {});

  if (slots.length === 0) {
    return (
      <div className={clsx('pf-p-4 pf-bg-gray-50 pf-rounded-xl pf-text-center', className)}>
        <p className="pf-text-gray-600 pf-text-sm">No available slots at this time.</p>
        <p className="pf-text-gray-500 pf-text-xs pf-mt-1">Please try a different date range.</p>
      </div>
    );
  }

  return (
    <div className={clsx('pf-p-4 pf-bg-gray-50 pf-rounded-xl', className)}>
      <p className="pf-text-sm pf-text-gray-700 pf-mb-4 pf-font-medium">
        Available appointment times
      </p>

      <div className="pf-space-y-4">
        {Object.entries(groupedSlots).map(([dateKey, dateSlots]) => (
          <div key={dateKey}>
            <p className="pf-text-xs pf-text-gray-500 pf-uppercase pf-tracking-wide pf-mb-2">
              {formatDate(new Date(dateKey))}
            </p>
            <div className="pf-grid pf-grid-cols-2 pf-gap-2">
              {dateSlots.map((slot) => (
                <button
                  key={slot.id}
                  onClick={() => onSelect(slot)}
                  className={clsx(
                    'pf-p-3 pf-rounded-lg pf-text-left pf-transition-all',
                    'pf-bg-white pf-border pf-border-gray-200',
                    'hover:pf-border-primary hover:pf-shadow-sm'
                  )}
                >
                  <p className="pf-text-sm pf-font-medium pf-text-gray-900">
                    {formatTime(slot.startTime)}
                  </p>
                  <p className="pf-text-xs pf-text-gray-500 pf-mt-1">
                    {slot.dentistName}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
