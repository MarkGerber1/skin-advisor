# WCAG Contrast Analysis Report

Generated: 02.09.2025, 02:57:47

## Overview

This report analyzes color contrast ratios for the Skincare Bot design system against WCAG 2.1 accessibility guidelines.

### WCAG Standards
- **AA Normal text**: 4.5:1 minimum ratio
- **AA Large text**: 3:1 minimum ratio (18px+ or 14px+ bold)
- **AAA Normal text**: 7:1 minimum ratio (enhanced)

## Results

| Status | Pair | Ratio | AA Normal | AA Large | AAA | Context |
|--------|------|-------|-----------|----------|-----|---------|
| 🟠 | Primary text on white | 3.66:1 | ❌ | ✅ | ❌ | Primary buttons, links |
| 🟢 | Body text on white | 18.73:1 | ✅ | ✅ | ✅ | Main content text |
| 🟡 | Muted text on white | 5.33:1 | ✅ | ✅ | ❌ | Secondary text, captions |
| 🟠 | White text on primary | 3.66:1 | ❌ | ✅ | ❌ | Primary button text |
| 🟢 | Body text on surface | 17.95:1 | ✅ | ✅ | ✅ | Card content |
| 🟢 | Body text on secondary | 14.46:1 | ✅ | ✅ | ✅ | Highlighted areas |
| 🟡 | White on success | 5.13:1 | ✅ | ✅ | ❌ | Success buttons |
| 🟠 | White on warning | 4.24:1 | ❌ | ✅ | ❌ | Warning buttons |
| 🟡 | White on danger | 6.54:1 | ✅ | ✅ | ❌ | Error buttons |
| 🟡 | White on info | 4.60:1 | ✅ | ✅ | ❌ | Info buttons |
| 🟢 | Dark: White text on dark bg (dark) | 18.73:1 | ✅ | ✅ | ✅ | Dark theme body text |
| 🟢 | Dark: Muted text on dark bg (dark) | 12.02:1 | ✅ | ✅ | ✅ | Dark theme secondary text |
| 🟢 | Dark: Text on dark surface (dark) | 17.22:1 | ✅ | ✅ | ✅ | Dark theme cards |
| 🟡 | Dark: Primary on dark bg (dark) | 5.12:1 | ✅ | ✅ | ❌ | Dark theme primary elements |
| 🟢 | Dark: Accent on dark bg (dark) | 11.80:1 | ✅ | ✅ | ✅ | Dark theme accents |
| 🔴 | Border on white | 1.21:1 | ❌ | ❌ | ❌ | Light theme borders |
| 🔴 | Dark: Border on dark bg (dark) | 1.31:1 | ❌ | ❌ | ❌ | Dark theme borders |

## Summary

- **Total pairs**: 17
- **AA compliant**: 12/17 (71%)
- **AAA compliant**: 7/17 (41%)
- **Failed**: 2/17 (12%)

## Color Palette

### Light Theme
- **Primary**: `#C26A8D` (Rose Mauve)
- **Secondary**: `#F4DCE4` (Nude Blush)  
- **Accent**: `#C9B7FF` (Soft Lilac)
- **Background**: `#FFFFFF`
- **Text**: `#121212`
- **Muted**: `#6B6B6B`

### Dark Theme
- **Background**: `#121212`
- **Text**: `#FFFFFF`
- **Muted**: `#CFCFCF`
- **Accent**: `#D4C5FF`

## Recommendations

1. **Primary color** (`#C26A8D`) should only be used for:
   - Accent elements and highlights
   - Icons and decorative elements
   - NOT for body text on white backgrounds

2. **Muted text** (`#6B6B6B`) is suitable for:
   - Secondary information
   - Captions and metadata
   - Non-critical content

3. **High contrast combinations** that work well:
   - White text on primary background
   - Dark text on white/light backgrounds
   - Dark theme provides excellent contrast ratios

4. **Failed combinations** should be avoided or only used for:
   - Decorative purposes
   - Non-text elements
   - Large text (18px+) where applicable
