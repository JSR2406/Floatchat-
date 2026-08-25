import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number | null | undefined, maxDecimals = 2): string {
  if (num === null || num === undefined || isNaN(num)) return '—';
  if (Math.abs(num) >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(maxDecimals)}M`;
  }
  if (Math.abs(num) >= 1_000) {
    return `${(num / 1_000).toFixed(maxDecimals)}K`;
  }
  return num.toLocaleString(undefined, { maximumFractionDigits: maxDecimals });
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function formatDateTime(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleString('en-IN', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export function getConfidenceColor(label: string): string {
  switch (label) {
    case 'high': return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    case 'medium': return 'text-amber-600 bg-amber-50 border-amber-200';
    case 'low': return 'text-rose-600 bg-rose-50 border-rose-200';
    default: return 'text-muted-foreground bg-muted border-border';
  }
}

export function getRiskColor(label: string): string {
  switch (label) {
    case 'low': return 'text-emerald-600 bg-emerald-50';
    case 'moderate': return 'text-amber-600 bg-amber-50';
    case 'elevated': return 'text-orange-600 bg-orange-50';
    case 'unavailable': return 'text-rose-600 bg-rose-50';
    default: return 'text-muted-foreground bg-muted';
  }
}