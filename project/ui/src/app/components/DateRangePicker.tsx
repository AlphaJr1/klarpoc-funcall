"use client";

import { useState, useRef, useEffect } from "react";
import { Calendar, X, ChevronLeft, ChevronRight } from "lucide-react";

interface DateRangePickerProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  className?: string;
}

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const DAYS   = ["Su","Mo","Tu","We","Th","Fr","Sa"];

function fmt(d: Date) {
  return d.toISOString().slice(0, 10);
}

function parseDate(s: string): Date | null {
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

export default function DateRangePicker({ value, onChange, placeholder, className }: DateRangePickerProps) {
  const [open, setOpen] = useState(false);
  const [rangeStart, setRangeStart] = useState<Date | null>(() => {
    if (!value) return null;
    const parts = value.split(" to ");
    return parseDate(parts[0]?.trim() || "");
  });
  const [rangeEnd, setRangeEnd]   = useState<Date | null>(() => {
    if (!value) return null;
    const parts = value.split(" to ");
    return parts[1] ? parseDate(parts[1].trim()) : null;
  });
  const [viewYear, setViewYear] = useState(() => {
    if (!value) return new Date().getFullYear();
    const parts = value.split(" to ");
    const s = parseDate(parts[0]?.trim() || "");
    return s ? s.getFullYear() : new Date().getFullYear();
  });
  const [viewMonth, setViewMonth] = useState(() => {
    if (!value) return new Date().getMonth();
    const parts = value.split(" to ");
    const s = parseDate(parts[0]?.trim() || "");
    return s ? s.getMonth() : new Date().getMonth();
  });
  const [hovered, setHovered]     = useState<Date | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  const [prevValue, setPrevValue] = useState(value);
  if (value !== prevValue) {
    setPrevValue(value);
    if (!value) {
      setRangeStart(null);
      setRangeEnd(null);
    } else {
      const parts = value.split(" to ");
      const s = parseDate(parts[0]?.trim() || "");
      const e = parts[1] ? parseDate(parts[1].trim()) : null;
      setRangeStart(s);
      setRangeEnd(e);
      if (s) {
        setViewYear(s.getFullYear());
        setViewMonth(s.getMonth());
      }
    }
  }

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1); }
    else setViewMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1); }
    else setViewMonth(m => m + 1);
  };

  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const firstDow    = new Date(viewYear, viewMonth, 1).getDay();

  const handleDayClick = (day: number) => {
    const clicked = new Date(viewYear, viewMonth, day);
    if (!rangeStart || (rangeStart && rangeEnd)) {
      setRangeStart(clicked);
      setRangeEnd(null);
      setHovered(null);
    } else {
      if (clicked < rangeStart) {
        setRangeEnd(rangeStart);
        setRangeStart(clicked);
        onChange(`${fmt(clicked)} to ${fmt(rangeStart)}`);
      } else if (fmt(clicked) === fmt(rangeStart)) {
        onChange(fmt(clicked));
        setRangeEnd(null);
        setOpen(false);
      } else {
        setRangeEnd(clicked);
        onChange(`${fmt(rangeStart)} to ${fmt(clicked)}`);
        setOpen(false);
      }
    }
  };

  const isInRange = (day: number) => {
    const d = new Date(viewYear, viewMonth, day);
    const end = rangeEnd || hovered;
    if (!rangeStart || !end) return false;
    const lo = rangeStart < end ? rangeStart : end;
    const hi = rangeStart < end ? end : rangeStart;
    return d > lo && d < hi;
  };
  const isStart = (day: number) => rangeStart && fmt(new Date(viewYear, viewMonth, day)) === fmt(rangeStart);
  const isEnd   = (day: number) => {
    const end = rangeEnd || (rangeStart ? hovered : null);
    return end && fmt(new Date(viewYear, viewMonth, day)) === fmt(end);
  };
  const isToday = (day: number) => fmt(new Date(viewYear, viewMonth, day)) === fmt(new Date());

  const clear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange("");
    setRangeStart(null);
    setRangeEnd(null);
  };

  return (
    <div ref={ref} className={`relative ${className ?? ""}`}>
      {/* Input row */}
      <div
        onClick={() => setOpen(o => !o)}
        className="flex items-center w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 gap-2 cursor-pointer focus-within:border-indigo-500 hover:border-gray-600 transition-colors group"
      >
        <Calendar className="w-4 h-4 text-gray-500 shrink-0" />
        <input
          type="text"
          placeholder={placeholder ?? "e.g. 2026-02-24 or 2026-01-01 to 2026-02-25"}
          value={value}
          onChange={e => onChange(e.target.value)}
          onClick={e => e.stopPropagation()}
          className="flex-1 bg-transparent text-sm text-gray-200 placeholder-gray-500 focus:outline-none min-w-0"
        />
        {value && (
          <button onClick={clear} className="text-gray-500 hover:text-gray-300">
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Calendar popover */}
      {open && (
        <div className="absolute left-0 top-[calc(100%+6px)] z-50 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-4 w-72 select-none">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm font-semibold text-white">{MONTHS[viewMonth]} {viewYear}</span>
            <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 mb-1">
            {DAYS.map(d => (
              <div key={d} className="text-center text-[10px] font-medium text-gray-500 py-1">{d}</div>
            ))}
          </div>

          {/* Days grid */}
          <div className="grid grid-cols-7 gap-y-0.5">
            {Array.from({ length: firstDow }).map((_, i) => <div key={`e${i}`} />)}
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map(day => {
              const start = isStart(day);
              const end   = isEnd(day);
              const inRange = isInRange(day);
              const today = isToday(day);
              return (
                <button
                  key={day}
                  onClick={() => handleDayClick(day)}
                  onMouseEnter={() => rangeStart && !rangeEnd && setHovered(new Date(viewYear, viewMonth, day))}
                  onMouseLeave={() => setHovered(null)}
                  className={`relative h-8 text-xs font-medium transition-colors rounded-lg
                    ${start || end ? "bg-indigo-600 text-white z-10" : ""}
                    ${inRange ? "bg-indigo-500/20 text-indigo-200 rounded-none" : ""}
                    ${!start && !end && !inRange ? "text-gray-300 hover:bg-gray-700 hover:text-white" : ""}
                    ${today && !start && !end ? "ring-1 ring-inset ring-indigo-400/60" : ""}
                  `}
                >
                  {day}
                </button>
              );
            })}
          </div>

          {/* Footer hint */}
          <p className="text-[10px] text-gray-600 text-center mt-3">
            {!rangeStart ? "Click to select start date" : !rangeEnd ? "Click to select end date (or same date for single)" : "Range selected"}
          </p>
        </div>
      )}
    </div>
  );
}
