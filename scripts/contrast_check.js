#!/usr/bin/env node

/**
 * WCAG Contrast Ratio Calculator
 * Beauty Care Design System
 *
 * Validates AA compliance for all color combinations
 * Usage: node scripts/contrast_check.js
 */

const fs = require('fs');
const path = require('path');

// Design system color definitions
const COLORS = {
  // Brand colors
  primary: '#C26A8D',
  secondary: '#F4DCE4',
  accent: '#C9B7FF',

  // Neutrals - Light theme
  lightBg: '#FFFFFF',
  lightFg: '#121212',
  lightMuted: '#6B6B6B',
  lightSurface: '#FAFAFA',
  lightBorder: '#E9E9E9',

  // Neutrals - Dark theme
  darkBg: '#121212',
  darkFg: '#FFFFFF',
  darkMuted: '#CFCFCF',
  darkSurface: '#1B1B1B',
  darkBorder: '#2A2A2A',

  // Semantic colors
  success: '#2E7D32',
  warning: '#B26A00',
  danger: '#B3261E'
};

/**
 * Convert hex color to RGB
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

/**
 * Calculate relative luminance
 */
function getRelativeLuminance(color) {
  const rgb = hexToRgb(color);
  if (!rgb) return 0;

  const { r, g, b } = rgb;

  // Convert to linear RGB
  const toLinear = (c) => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  };

  const rLinear = toLinear(r);
  const gLinear = toLinear(g);
  const bLinear = toLinear(b);

  // Calculate luminance
  return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear;
}

/**
 * Calculate contrast ratio between two colors
 */
function getContrastRatio(color1, color2) {
  const lum1 = getRelativeLuminance(color1);
  const lum2 = getRelativeLuminance(color2);

  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check WCAG compliance
 */
function checkWCAGCompliance(ratio, isLargeText = false) {
  const aaNormal = 4.5;
  const aaLarge = 3.0;
  const aaaNormal = 7.0;
  const aaaLarge = 4.5;

  const threshold = isLargeText ? aaLarge : aaNormal;
  const aaaThreshold = isLargeText ? aaaLarge : aaaNormal;

  const aa = ratio >= threshold;
  const aaa = ratio >= aaaThreshold;

  return {
    ratio: ratio.toFixed(2),
    aa,
    aaa,
    aaThreshold: threshold,
    aaaThreshold: aaaThreshold
  };
}

/**
 * Generate comprehensive contrast report
 */
function generateContrastReport() {
  console.log('🎨 BEAUTY CARE DESIGN SYSTEM - WCAG CONTRAST REPORT');
  console.log('='.repeat(70));
  console.log('');

  const results = [];
  let totalTests = 0;
  let aaPassed = 0;
  let aaaPassed = 0;

  // Define test combinations
  const combinations = [
    // Light Theme Text Combinations
    { name: 'Primary Text on Light BG', fg: COLORS.lightFg, bg: COLORS.lightBg, isLarge: false },
    { name: 'Secondary Text on Light BG', fg: COLORS.lightMuted, bg: COLORS.lightBg, isLarge: false },
    { name: 'Primary Text Large on Light BG', fg: COLORS.lightFg, bg: COLORS.lightBg, isLarge: true },
    { name: 'Secondary Text Large on Light BG', fg: COLORS.lightMuted, bg: COLORS.lightBg, isLarge: true },

    // Dark Theme Text Combinations
    { name: 'Primary Text on Dark BG', fg: COLORS.darkFg, bg: COLORS.darkBg, isLarge: false },
    { name: 'Secondary Text on Dark BG', fg: COLORS.darkMuted, bg: COLORS.darkBg, isLarge: false },
    { name: 'Primary Text Large on Dark BG', fg: COLORS.darkFg, bg: COLORS.darkBg, isLarge: true },
    { name: 'Secondary Text Large on Dark BG', fg: COLORS.darkMuted, bg: COLORS.darkBg, isLarge: true },

    // Button Combinations - Light Theme
    { name: 'Primary Button Text on Primary BG', fg: '#FFFFFF', bg: COLORS.primary, isLarge: false },
    { name: 'Secondary Button Text on Surface', fg: COLORS.lightFg, bg: COLORS.lightSurface, isLarge: false },
    { name: 'Accent Button Text on Accent BG', fg: COLORS.lightBg, bg: COLORS.accent, isLarge: false },

    // Button Combinations - Dark Theme
    { name: 'Primary Button Text on Primary BG (Dark)', fg: '#FFFFFF', bg: COLORS.primary, isLarge: false },
    { name: 'Secondary Button Text on Dark Surface', fg: COLORS.darkFg, bg: COLORS.darkSurface, isLarge: false },
    { name: 'Accent Button Text on Accent BG (Dark)', fg: COLORS.darkBg, bg: COLORS.accent, isLarge: false },

    // Interactive Elements
    { name: 'Link Text on Light BG', fg: COLORS.primary, bg: COLORS.lightBg, isLarge: false },
    { name: 'Link Text on Dark BG', fg: COLORS.primary, bg: COLORS.darkBg, isLarge: false },

    // Surface Combinations
    { name: 'Card on Light BG', fg: COLORS.lightSurface, bg: COLORS.lightBg, isLarge: false },
    { name: 'Card on Dark BG', fg: COLORS.darkSurface, bg: COLORS.darkBg, isLarge: false },
    { name: 'Border on Light BG', fg: COLORS.lightBorder, bg: COLORS.lightBg, isLarge: false },
    { name: 'Border on Dark BG', fg: COLORS.darkBorder, bg: COLORS.darkBg, isLarge: false }
  ];

  // Test each combination
  combinations.forEach(combo => {
    totalTests++;
    const ratio = getContrastRatio(combo.fg, combo.bg);
    const compliance = checkWCAGCompliance(ratio, combo.isLarge);

    const result = {
      name: combo.name,
      ratio: compliance.ratio,
      aa: compliance.aa,
      aaa: compliance.aaa,
      isLarge: combo.isLarge,
      fg: combo.fg,
      bg: combo.bg
    };

    results.push(result);

    if (compliance.aa) aaPassed++;
    if (compliance.aaa) aaaPassed++;
  });

  // Display results
  console.log('📊 CONTRAST RATIOS BY CATEGORY:');
  console.log('-'.repeat(50));

  const categories = ['Light Theme Text', 'Dark Theme Text', 'Buttons (Light)', 'Buttons (Dark)', 'Interactive', 'Surfaces'];

  let currentCategory = '';
  results.forEach(result => {
    const category = result.name.includes('Light') && result.name.includes('Text') ? 'Light Theme Text' :
                    result.name.includes('Dark') && result.name.includes('Text') ? 'Dark Theme Text' :
                    result.name.includes('Button') && result.name.includes('Light') ? 'Buttons (Light)' :
                    result.name.includes('Button') && result.name.includes('Dark') ? 'Buttons (Dark)' :
                    result.name.includes('Link') ? 'Interactive' : 'Surfaces';

    if (category !== currentCategory) {
      console.log(`\n${category}:`);
      currentCategory = category;
    }

    const status = result.aa ? (result.aaa ? '✅ AAA' : '✅ AA') : '❌ FAIL';
    const size = result.isLarge ? 'Large' : 'Normal';
    console.log(`  ${result.name}: ${result.ratio}:1 ${status} (${size})`);
  });

  // Summary
  console.log('\n' + '='.repeat(70));
  console.log('📈 SUMMARY:');
  console.log(`Total Tests: ${totalTests}`);
  console.log(`AA Compliant: ${aaPassed}/${totalTests} (${Math.round(aaPassed/totalTests*100)}%)`);
  console.log(`AAA Compliant: ${aaaPassed}/${totalTests} (${Math.round(aaaPassed/totalTests*100)}%)`);

  // Critical failures
  const failures = results.filter(r => !r.aa);
  if (failures.length > 0) {
    console.log('\n🚨 CRITICAL FAILURES:');
    failures.forEach(failure => {
      console.log(`  ❌ ${failure.name}: ${failure.ratio}:1 (needs ${failure.isLarge ? '3.0' : '4.5'}:1)`);
    });

    console.log('\n💡 RECOMMENDATIONS:');
    console.log('  • Increase contrast by darkening backgrounds or lightening text');
    console.log('  • Use larger text sizes for better accessibility');
    console.log('  • Test with actual users for readability');
  }

  console.log('\n🎯 ACCESSIBILITY SCORE:');
  const score = aaPassed/totalTests;
  if (score >= 0.9) console.log('  🏆 EXCELLENT: 90%+ AA compliance');
  else if (score >= 0.8) console.log('  ✅ GOOD: 80%+ AA compliance');
  else if (score >= 0.7) console.log('  ⚠️ FAIR: 70%+ AA compliance');
  else console.log('  🚨 NEEDS IMPROVEMENT: <70% AA compliance');

  console.log('\n✅ REPORT GENERATED SUCCESSFULLY');
  console.log('='.repeat(70));

  return results;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getContrastRatio,
    checkWCAGCompliance,
    generateContrastReport,
    COLORS
  };
}

// Run if called directly
if (require.main === module) {
  generateContrastReport();
}