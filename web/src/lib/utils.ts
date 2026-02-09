/**
 * Utility functions for the frontend application.
 *
 * @module utils
 * @description Provides commonly used utility functions including
 * class name merging utilities for Tailwind CSS.
 */

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Merges class names with Tailwind CSS conflict resolution.
 *
 * @description Combines clsx for conditional class handling with tailwind-merge
 * for proper Tailwind CSS class deduplication and conflict resolution.
 * This is the standard pattern for dynamic className handling in Tailwind projects.
 *
 * @param inputs - Class values to merge (strings, objects, arrays, conditionals)
 * @returns Merged class string with Tailwind conflicts resolved
 *
 * @example
 * ```typescript
 * // Basic usage
 * cn("px-2 py-1", "px-4") // "py-1 px-4" (px-4 wins)
 *
 * // Conditional classes
 * cn("base-class", isActive && "active-class")
 *
 * // Object syntax
 * cn({ "text-red-500": hasError, "text-green-500": !hasError })
 * ```
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
