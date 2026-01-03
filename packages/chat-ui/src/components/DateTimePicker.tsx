import { useState } from 'react';
import { clsx } from 'clsx';

interface DateTimePickerProps {
  onSelect: (date: Date) => void;
  availableDates?: Date[];
  className?: string;
}

/**
 * Date and time picker component for appointment scheduling.
 */
export function DateTimePicker({ onSelect, availableDates, className }: DateTimePickerProps): JSX.Element {
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);

  const today = new Date();
  const dates = availableDates || Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() + i + 1);
    return date;
  });

  const timeSlots = [
    '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM',
    '11:00 AM', '11:30 AM', '2:00 PM', '2:30 PM',
    '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM',
  ];

  const handleSubmit = () => {
    if (selectedDate && selectedTime) {
      const [time, period] = selectedTime.split(' ');
      const [hours, minutes] = time.split(':').map(Number);
      const adjustedHours = period === 'PM' && hours !== 12 ? hours + 12 : hours;

      const dateTime = new Date(selectedDate);
      dateTime.setHours(adjustedHours, minutes, 0, 0);
      onSelect(dateTime);
    }
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-AU', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className={clsx('pf-p-4 pf-bg-gray-50 pf-rounded-xl', className)}>
      <p className="pf-text-sm pf-text-gray-700 pf-mb-4 pf-font-medium">
        Select a date and time for your appointment
      </p>

      {/* Date selection */}
      <div className="pf-mb-4">
        <label className="pf-text-xs pf-text-gray-500 pf-uppercase pf-tracking-wide pf-mb-2 pf-block">
          Date
        </label>
        <div className="pf-flex pf-flex-wrap pf-gap-2">
          {dates.slice(0, 5).map((date, index) => (
            <button
              key={index}
              onClick={() => setSelectedDate(date)}
              className={clsx(
                'pf-px-3 pf-py-2 pf-rounded-lg pf-text-sm pf-transition-colors',
                selectedDate?.toDateString() === date.toDateString()
                  ? 'pf-bg-primary pf-text-white'
                  : 'pf-bg-white pf-border pf-border-gray-200 hover:pf-border-primary'
              )}
            >
              {formatDate(date)}
            </button>
          ))}
        </div>
      </div>

      {/* Time selection */}
      {selectedDate && (
        <div className="pf-mb-4">
          <label className="pf-text-xs pf-text-gray-500 pf-uppercase pf-tracking-wide pf-mb-2 pf-block">
            Time
          </label>
          <div className="pf-grid pf-grid-cols-3 pf-gap-2">
            {timeSlots.map((time) => (
              <button
                key={time}
                onClick={() => setSelectedTime(time)}
                className={clsx(
                  'pf-px-3 pf-py-2 pf-rounded-lg pf-text-sm pf-transition-colors',
                  selectedTime === time
                    ? 'pf-bg-primary pf-text-white'
                    : 'pf-bg-white pf-border pf-border-gray-200 hover:pf-border-primary'
                )}
              >
                {time}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Submit button */}
      {selectedDate && selectedTime && (
        <button
          onClick={handleSubmit}
          className="pf-w-full pf-py-2 pf-px-4 pf-bg-primary pf-text-white pf-rounded-full pf-text-sm pf-font-medium hover:pf-bg-primary/90 pf-transition-colors"
        >
          Confirm: {formatDate(selectedDate)} at {selectedTime}
        </button>
      )}
    </div>
  );
}
