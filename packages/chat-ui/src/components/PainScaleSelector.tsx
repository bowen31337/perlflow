import React, { useState } from 'react';
import { clsx } from 'clsx';

interface PainScaleSelectorProps {
  onSelect: (value: number) => void;
  className?: string;
}

/**
 * Pain scale selector component for triage flow.
 * Displays a 1-10 slider with color gradient.
 */
export function PainScaleSelector({ onSelect, className }: PainScaleSelectorProps): JSX.Element {
  const [value, setValue] = useState<number>(5);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const getPainLabel = (level: number): string => {
    if (level <= 2) return 'Minimal';
    if (level <= 4) return 'Mild';
    if (level <= 6) return 'Moderate';
    if (level <= 8) return 'Severe';
    return 'Worst possible';
  };

  const getGradientColor = (level: number): string => {
    if (level <= 2) return '#22C55E'; // Green
    if (level <= 4) return '#84CC16'; // Lime
    if (level <= 6) return '#EAB308'; // Yellow
    if (level <= 8) return '#F97316'; // Orange
    return '#EF4444'; // Red
  };

  const handleSubmit = () => {
    setIsSubmitted(true);
    onSelect(value);
  };

  if (isSubmitted) {
    return (
      <div className={clsx('pf-p-4 pf-bg-gray-50 pf-rounded-xl', className)}>
        <div className="pf-text-center">
          <span className="pf-text-2xl">{value}/10</span>
          <p className="pf-text-sm pf-text-gray-600 pf-mt-1">{getPainLabel(value)} pain</p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('pf-p-4 pf-bg-gray-50 pf-rounded-xl', className)}>
      <p className="pf-text-sm pf-text-gray-700 pf-mb-4 pf-font-medium">
        On a scale of 1-10, how would you rate your pain?
      </p>

      {/* Pain scale slider */}
      <div className="pf-space-y-4">
        {/* Number labels */}
        <div className="pf-flex pf-justify-between pf-text-xs pf-text-gray-500">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
            <span key={num}>{num}</span>
          ))}
        </div>

        {/* Slider */}
        <input
          type="range"
          min="1"
          max="10"
          value={value}
          onChange={(e) => setValue(parseInt(e.target.value, 10))}
          className="pf-w-full pf-h-3 pf-rounded-full pf-appearance-none pf-cursor-pointer"
          style={{
            background: `linear-gradient(to right, #22C55E, #84CC16, #EAB308, #F97316, #EF4444)`,
          }}
        />

        {/* Current value display */}
        <div className="pf-text-center">
          <span
            className="pf-text-3xl pf-font-bold"
            style={{ color: getGradientColor(value) }}
          >
            {value}
          </span>
          <p className="pf-text-sm pf-text-gray-600 pf-mt-1">{getPainLabel(value)}</p>
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          className="pf-w-full pf-py-2 pf-px-4 pf-bg-primary pf-text-white pf-rounded-full pf-text-sm pf-font-medium hover:pf-bg-primary/90 pf-transition-colors"
        >
          Confirm
        </button>
      </div>
    </div>
  );
}
