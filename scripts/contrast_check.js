#!/usr/bin/env node

/**
 * WCAG Contrast Ratio Calculator
 * Beauty & Skincare Chatbot Design System
 *
 * Usage: node scripts/contrast_check.js
 */

const fs = require('fs');
const path = require('path');

// Color definitions from our design tokens
const COLORS = {
  // Brand colors
  primary: '#C26A8D',
  primaryHover: '#A8577A',
  primaryLight: '#E5B8C8',
  primaryDark: '#9E556D',

  secondary: '#F4DCE4',
  secondaryHover: '#E8C8D1',
  secondaryLight: '#F9ECF0',
  secondaryDark: '#E8BFC7',

  accent: '#C9B7FF',
  accentHover: '#B39BFF',
  accentLight: '#E3DDFF',
  accentDark: '#A390E6',

  // Light theme neutrals
  lightBg: '#FFFFFF',
  lightBgSecondary: '#F8F9FA',
  lightBgTertiary: '#E9ECEF',
  lightFgPrimary: '#212529',
  lightFgSecondary: '#6C757D',
  lightFgTertiary: '#ADB5BD',
  lightBorder: '#DEE2E6',
  lightSurface: '#FFFFFF',

  // Dark theme neutrals
  darkBg: '#121212',
  darkBgSecondary: '#1E1E1E',
  darkBgTertiary: '#2A2A2A',
  darkFgPrimary: '#FFFFFF',
  darkFgSecondary: '#CCCCCC',
  darkFgTertiary: '#999999',
  darkBorder: '#333333',
  darkSurface: '#1E1E1E',

  // Semantic colors
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#F44336',
  info: '#2196F3'
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

  return { aa, aaa, ratio: ratio.toFixed(2) };
}

/**
 * Generate contrast report
 */
function generateContrastReport() {
  console.log('='.repeat(80));
  console.log('🎨 BEAUTY CHATBOT DESIGN SYSTEM - WCAG CONTRAST REPORT');
  console.log('='.repeat(80));
  console.log('');

  const results = [];

  // Primary Button Combinations
  console.log('🏠 PRIMARY BUTTONS');
  console.log('-'.repeat(40));

  const primaryButtonLight = checkWCAGCompliance(
    getContrastRatio(COLORS.primary, COLORS.lightBg),
    false
  );
  console.log(`Primary on Light BG: ${primaryButtonLight.ratio}:1 ${primaryButtonLight.aa ? '✅ AA' : '❌ AA'} ${primaryButtonLight.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Primary Button (Light)', ...primaryButtonLight });

  const primaryButtonDark = checkWCAGCompliance(
    getContrastRatio(COLORS.primary, COLORS.darkSurface),
    false
  );
  console.log(`Primary on Dark BG: ${primaryButtonDark.ratio}:1 ${primaryButtonDark.aa ? '✅ AA' : '❌ AA'} ${primaryButtonDark.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Primary Button (Dark)', ...primaryButtonDark });

  // Secondary Button Combinations
  console.log('');
  console.log('🔄 SECONDARY BUTTONS');
  console.log('-'.repeat(40));

  const secondaryButtonLight = checkWCAGCompliance(
    getContrastRatio(COLORS.secondary, COLORS.lightBg),
    false
  );
  console.log(`Secondary on Light BG: ${secondaryButtonLight.ratio}:1 ${secondaryButtonLight.aa ? '✅ AA' : '❌ AA'} ${secondaryButtonLight.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Secondary Button (Light)', ...secondaryButtonLight });

  const secondaryButtonDark = checkWCAGCompliance(
    getContrastRatio(COLORS.secondary, COLORS.darkSurface),
    false
  );
  console.log(`Secondary on Dark BG: ${secondaryButtonDark.ratio}:1 ${secondaryButtonDark.aa ? '✅ AA' : '❌ AA'} ${secondaryButtonDark.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Secondary Button (Dark)', ...secondaryButtonDark });

  // Accent Button Combinations
  console.log('');
  console.log('✨ ACCENT BUTTONS');
  console.log('-'.repeat(40));

  const accentButtonLight = checkWCAGCompliance(
    getContrastRatio(COLORS.accent, COLORS.lightBg),
    false
  );
  console.log(`Accent on Light BG: ${accentButtonLight.ratio}:1 ${accentButtonLight.aa ? '✅ AA' : '❌ AA'} ${accentButtonLight.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Accent Button (Light)', ...accentButtonLight });

  const accentButtonDark = checkWCAGCompliance(
    getContrastRatio(COLORS.accent, COLORS.darkSurface),
    false
  );
  console.log(`Accent on Dark BG: ${accentButtonDark.ratio}:1 ${accentButtonDark.aa ? '✅ AA' : '❌ AA'} ${accentButtonDark.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Accent Button (Dark)', ...accentButtonDark });

  // Text Combinations
  console.log('');
  console.log('📝 TEXT CONTRAST');
  console.log('-'.repeat(40));

  const primaryTextLight = checkWCAGCompliance(
    getContrastRatio(COLORS.lightFgPrimary, COLORS.lightBg),
    false
  );
  console.log(`Primary Text on Light BG: ${primaryTextLight.ratio}:1 ${primaryTextLight.aa ? '✅ AA' : '❌ AA'} ${primaryTextLight.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Primary Text (Light)', ...primaryTextLight });

  const primaryTextDark = checkWCAGCompliance(
    getContrastRatio(COLORS.darkFgPrimary, COLORS.darkBg),
    false
  );
  console.log(`Primary Text on Dark BG: ${primaryTextDark.ratio}:1 ${primaryTextDark.aa ? '✅ AA' : '❌ AA'} ${primaryTextDark.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Primary Text (Dark)', ...primaryTextDark });

  const secondaryTextLight = checkWCAGCompliance(
    getContrastRatio(COLORS.lightFgSecondary, COLORS.lightBg),
    false
  );
  console.log(`Secondary Text on Light BG: ${secondaryTextLight.ratio}:1 ${secondaryTextLight.aa ? '✅ AA' : '❌ AA'} ${secondaryTextLight.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Secondary Text (Light)', ...secondaryTextLight });

  const secondaryTextDark = checkWCAGCompliance(
    getContrastRatio(COLORS.darkFgSecondary, COLORS.darkBg),
    false
  );
  console.log(`Secondary Text on Dark BG: ${secondaryTextDark.ratio}:1 ${secondaryTextDark.aa ? '✅ AA' : '❌ AA'} ${secondaryTextDark.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Secondary Text (Dark)', ...secondaryTextDark });

  // Large Text Combinations (18pt+ or 14pt+ bold)
  console.log('');
  console.log('📊 LARGE TEXT CONTRAST (18pt+, 14pt+ bold)');
  console.log('-'.repeat(40));

  const largeTextLight = checkWCAGCompliance(
    getContrastRatio(COLORS.lightFgPrimary, COLORS.lightBg),
    true
  );
  console.log(`Large Text on Light BG: ${largeTextLight.ratio}:1 ${largeTextLight.aa ? '✅ AA' : '❌ AA'} ${largeTextLight.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Large Text (Light)', ...largeTextLight });

  const largeTextDark = checkWCAGCompliance(
    getContrastRatio(COLORS.darkFgPrimary, COLORS.darkBg),
    true
  );
  console.log(`Large Text on Dark BG: ${largeTextDark.ratio}:1 ${largeTextDark.aa ? '✅ AA' : '❌ AA'} ${largeTextDark.aaa ? '✅ AAA' : '❌ AAA'}`);
  results.push({ name: 'Large Text (Dark)', ...largeTextDark });

  // Summary
  console.log('');
  console.log('='.repeat(80));
  console.log('📊 SUMMARY');
  console.log('='.repeat(80));

  const totalTests = results.length;
  const aaPassed = results.filter(r => r.aa).length;
  const aaaPassed = results.filter(r => r.aaa).length;

  console.log(`Total Tests: ${totalTests}`);
  console.log(`AA Compliant: ${aaPassed}/${totalTests} (${Math.round(aaPassed/totalTests*100)}%)`);
  console.log(`AAA Compliant: ${aaaPassed}/${totalTests} (${Math.round(aaaPassed/totalTests*100)}%)`);

  // Check for failures
  const failures = results.filter(r => !r.aa);
  if (failures.length > 0) {
    console.log('');
    console.log('⚠️  AA FAILURES:');
    failures.forEach(failure => {
      console.log(`   ❌ ${failure.name}: ${failure.ratio}:1`);
    });
  }

  console.log('');
  console.log('✅ REPORT GENERATED SUCCESSFULLY');
  console.log('='.repeat(80));

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